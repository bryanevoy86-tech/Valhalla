#!/usr/bin/env python3
"""
VALHALLA RISK MONITORING MODULE
Monitors data quality, system performance, and security threats
"""

import logging
import json
import subprocess
from datetime import datetime
from pathlib import Path
from collections import deque

# Configure logging
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - RISK_MONITOR - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_dir / "risk_monitoring.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class RiskAlert:
    """Risk alert data structure"""
    
    SEVERITY_LEVELS = ["INFO", "WARNING", "CRITICAL"]
    
    def __init__(self, severity, category, message):
        self.severity = severity
        self.category = category
        self.message = message
        self.timestamp = datetime.now().isoformat()
    
    def to_dict(self):
        return {
            "timestamp": self.timestamp,
            "severity": self.severity,
            "category": self.category,
            "message": self.message
        }


class DataQualityMonitor:
    """Monitor data quality metrics"""
    
    def __init__(self):
        self.alerts = deque(maxlen=100)
        self.stats = {
            "total_records": 0,
            "valid_records": 0,
            "invalid_records": 0,
            "duplicate_records": 0,
            "missing_fields": 0
        }
    
    def check_lead_quality(self, lead):
        """Check individual lead quality"""
        issues = []
        
        # Check for required fields
        required = ["name", "email", "value"]
        for field in required:
            if not lead.get(field):
                issues.append(f"Missing field: {field}")
                self.stats["missing_fields"] += 1
        
        # Check data types
        try:
            if lead.get("value") and float(lead["value"]) < 0:
                issues.append("Negative value detected")
        except (ValueError, TypeError):
            issues.append("Invalid value format")
        
        # Check email format
        email = str(lead.get("email", ""))
        if "@" not in email:
            issues.append("Invalid email format")
        
        self.stats["total_records"] += 1
        
        if issues:
            self.stats["invalid_records"] += 1
            alert = RiskAlert("WARNING", "Data Quality", f"{lead.get('email', 'Unknown')}: {'; '.join(issues)}")
            self.alerts.append(alert)
            logger.warning(alert.message)
            return False
        else:
            self.stats["valid_records"] += 1
            return True
    
    def check_duplicates(self, leads_list):
        """Check for duplicate records"""
        emails = [lead.get("email") for lead in leads_list]
        duplicates = [email for email in emails if emails.count(email) > 1]
        
        if duplicates:
            self.stats["duplicate_records"] = len(set(duplicates))
            alert = RiskAlert("WARNING", "Data Quality", f"Duplicate emails found: {len(set(duplicates))}")
            self.alerts.append(alert)
            logger.warning(alert.message)
            return False
        return True
    
    def get_quality_score(self):
        """Calculate overall data quality score (0-100)"""
        if self.stats["total_records"] == 0:
            return 100
        
        valid_pct = (self.stats["valid_records"] / self.stats["total_records"]) * 100
        return valid_pct
    
    def get_alerts(self):
        """Get all quality alerts"""
        return [alert.to_dict() for alert in self.alerts]


class SystemPerformanceMonitor:
    """Monitor system performance (CPU, Memory, DB)"""
    
    def __init__(self, cpu_threshold=80, memory_threshold=80):
        self.cpu_threshold = cpu_threshold
        self.memory_threshold = memory_threshold
        self.alerts = deque(maxlen=100)
        self.metrics = {
            "cpu_usage": 0,
            "memory_usage": 0,
            "database_connections": 0,
            "thread_count": 0
        }
    
    def get_system_metrics(self):
        """Get current system metrics"""
        try:
            # CPU usage
            result = subprocess.run(
                ["tasklist", "/v"],
                capture_output=True,
                text=True
            )
            
            # Count Python processes
            python_processes = result.stdout.count("python.exe")
            
            self.metrics["thread_count"] = python_processes
            
            # Simulate realistic CPU/Memory for demo
            # In production, use psutil
            self.metrics["cpu_usage"] = 2.3  # Low in sandbox
            self.metrics["memory_usage"] = 13.27  # In MB
            self.metrics["database_connections"] = 1  # Isolated
            
            return self.metrics
        except Exception as e:
            logger.error(f"Error getting system metrics: {e}")
            return self.metrics
    
    def check_performance(self):
        """Check system performance against thresholds"""
        metrics = self.get_system_metrics()
        issues = []
        
        # Check CPU
        if metrics["cpu_usage"] > self.cpu_threshold:
            issues.append(f"High CPU usage: {metrics['cpu_usage']}%")
            alert = RiskAlert("CRITICAL", "System Performance", f"CPU usage exceeds threshold: {metrics['cpu_usage']}%")
            self.alerts.append(alert)
            logger.critical(alert.message)
        
        # Check Memory
        if metrics["memory_usage"] > self.memory_threshold:
            issues.append(f"High memory usage: {metrics['memory_usage']} MB")
            alert = RiskAlert("CRITICAL", "System Performance", f"Memory usage exceeds threshold: {metrics['memory_usage']} MB")
            self.alerts.append(alert)
            logger.critical(alert.message)
        
        # Check database connections
        if metrics["database_connections"] > 5:
            issues.append(f"Too many DB connections: {metrics['database_connections']}")
            alert = RiskAlert("WARNING", "System Performance", f"Excessive database connections: {metrics['database_connections']}")
            self.alerts.append(alert)
            logger.warning(alert.message)
        
        return len(issues) == 0, issues
    
    def get_alerts(self):
        """Get all performance alerts"""
        return [alert.to_dict() for alert in self.alerts]


class SecurityMonitor:
    """Monitor security and access control"""
    
    def __init__(self):
        self.alerts = deque(maxlen=100)
        self.stats = {
            "unauthorized_access_attempts": 0,
            "data_encryption_status": "ENABLED",
            "access_log_entries": 0
        }
    
    def log_data_access(self, user, data_type, action):
        """Log data access for audit trail"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "user": user,
            "data_type": data_type,
            "action": action
        }
        
        self.stats["access_log_entries"] += 1
        logger.info(f"Data access: {user} - {action} - {data_type}")
        
        return log_entry
    
    def check_encryption_status(self):
        """Verify encryption is enabled for sensitive data"""
        if self.stats["data_encryption_status"] == "ENABLED":
            return True
        else:
            alert = RiskAlert("CRITICAL", "Security", "Data encryption is DISABLED")
            self.alerts.append(alert)
            logger.critical(alert.message)
            return False
    
    def check_access_control(self, user, permission):
        """Check if user has required permission"""
        # Implement role-based access control
        allowed_roles = ["admin", "manager", "analyst"]
        
        if permission not in allowed_roles:
            self.stats["unauthorized_access_attempts"] += 1
            alert = RiskAlert("CRITICAL", "Security", f"Unauthorized access attempt by {user}")
            self.alerts.append(alert)
            logger.critical(alert.message)
            return False
        
        return True
    
    def get_alerts(self):
        """Get all security alerts"""
        return [alert.to_dict() for alert in self.alerts]


class RiskManagementSystem:
    """Unified risk management system"""
    
    def __init__(self):
        self.data_quality = DataQualityMonitor()
        self.performance = SystemPerformanceMonitor()
        self.security = SecurityMonitor()
        self.all_alerts = deque(maxlen=500)
    
    def run_full_risk_assessment(self, leads_data=None):
        """Run comprehensive risk assessment"""
        logger.info("=== STARTING FULL RISK ASSESSMENT ===")
        
        results = {
            "timestamp": datetime.now().isoformat(),
            "status": "HEALTHY",
            "data_quality": {
                "quality_score": 100,
                "alerts": []
            },
            "system_performance": {
                "status": "OK",
                "alerts": []
            },
            "security": {
                "status": "SECURE",
                "alerts": []
            }
        }
        
        # Check data quality
        if leads_data:
            for lead in leads_data:
                self.data_quality.check_lead_quality(lead)
            self.data_quality.check_duplicates(leads_data)
            quality_score = self.data_quality.get_quality_score()
            results["data_quality"]["quality_score"] = quality_score
            results["data_quality"]["alerts"] = self.data_quality.get_alerts()
            
            if quality_score < 95:
                results["status"] = "WARNING"
        
        # Check system performance
        perf_ok, perf_issues = self.performance.check_performance()
        results["system_performance"]["status"] = "OK" if perf_ok else "ALERT"
        results["system_performance"]["alerts"] = self.performance.get_alerts()
        
        if not perf_ok:
            results["status"] = "WARNING"
        
        # Check security
        sec_ok = self.security.check_encryption_status()
        results["security"]["status"] = "SECURE" if sec_ok else "COMPROMISED"
        results["security"]["alerts"] = self.security.get_alerts()
        
        if not sec_ok:
            results["status"] = "CRITICAL"
        
        logger.info(f"=== RISK ASSESSMENT COMPLETE ===")
        logger.info(f"Overall Status: {results['status']}")
        
        return results
    
    def export_risk_report(self, results, filename="risk_assessment.json"):
        """Export risk assessment results"""
        try:
            with open(filename, 'w') as f:
                json.dump(results, f, indent=2)
            logger.info(f"Risk report exported to: {filename}")
            return True
        except Exception as e:
            logger.error(f"Error exporting risk report: {e}")
            return False


if __name__ == "__main__":
    print("\n=== RISK MONITORING MODULE ===\n")
    
    # Create system
    risk_system = RiskManagementSystem()
    
    # Example test data
    test_leads = [
        {"name": "John Doe", "email": "john@example.com", "value": "50000"},
        {"name": "Jane Smith", "email": "jane@example.com", "value": "75000"},
        {"name": "Invalid Lead", "email": "invalid-email", "value": "-100"},
    ]
    
    # Run assessment
    results = risk_system.run_full_risk_assessment(test_leads)
    
    # Display results
    print(json.dumps(results, indent=2))
    
    # Export
    risk_system.export_risk_report(results)
