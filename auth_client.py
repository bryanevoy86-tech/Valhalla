"""
Valhalla Authentication Client
Testing and Demo Client for Authentication Service
"""

import requests
import json
import time
from typing import Optional, Dict, Any
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("Auth_Client")

# ============================================================================
# CONFIGURATION
# ============================================================================

BASE_URL = "http://localhost:8000"
USERNAME = "The All father"
PASSWORD = "IAmBatman!1"


class ValhallAuthClient:
    """Client for interacting with Valhalla Authentication Service"""
    
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.access_token: Optional[str] = None
        self.refresh_token: Optional[str] = None
        self.headers: Dict[str, str] = {"Content-Type": "application/json"}
    
    def login(self, username: str, password: str) -> bool:
        """
        Authenticate and obtain access and refresh tokens.
        
        Args:
            username: Username for authentication
            password: Password for authentication
            
        Returns:
            True if authentication successful, False otherwise
        """
        try:
            url = f"{self.base_url}/token"
            data = {"username": username, "password": password}
            
            response = requests.post(url, json=data)
            response.raise_for_status()
            
            result = response.json()
            self.access_token = result.get("access_token")
            self.refresh_token = result.get("refresh_token")
            
            # Update headers with bearer token
            self.headers["Authorization"] = f"Bearer {self.access_token}"
            
            logger.info(f"✅ Login successful for user: {username}")
            logger.info(f"   Access token expires in: {result.get('expires_in')} seconds")
            return True
            
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Login failed: {e}")
            return False
    
    def refresh_access_token(self) -> bool:
        """
        Refresh the access token using the refresh token.
        
        Returns:
            True if refresh successful, False otherwise
        """
        if not self.refresh_token:
            logger.error("❌ No refresh token available")
            return False
        
        try:
            url = f"{self.base_url}/refresh"
            headers = {"Authorization": f"Bearer {self.refresh_token}"}
            
            response = requests.post(url, headers=headers)
            response.raise_for_status()
            
            result = response.json()
            self.access_token = result.get("access_token")
            self.headers["Authorization"] = f"Bearer {self.access_token}"
            
            logger.info(f"✅ Access token refreshed")
            logger.info(f"   New token expires in: {result.get('expires_in')} seconds")
            return True
            
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Token refresh failed: {e}")
            return False
    
    def get_secure_data(self) -> Optional[Dict[str, Any]]:
        """
        Access protected endpoint for secure data.
        
        Returns:
            Secure data response or None if request fails
        """
        if not self.access_token:
            logger.error("❌ Not authenticated. Please login first.")
            return None
        
        try:
            url = f"{self.base_url}/secure-data/"
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"✅ Secure data retrieved")
            return result
            
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Failed to retrieve secure data: {e}")
            return None
    
    def get_user_profile(self) -> Optional[Dict[str, Any]]:
        """
        Get user profile information.
        
        Returns:
            User profile data or None if request fails
        """
        if not self.access_token:
            logger.error("❌ Not authenticated. Please login first.")
            return None
        
        try:
            url = f"{self.base_url}/user-profile/"
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"✅ User profile retrieved")
            return result
            
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Failed to retrieve user profile: {e}")
            return None
    
    def get_protected_resource(self) -> Optional[Dict[str, Any]]:
        """
        Access protected resource.
        
        Returns:
            Protected resource data or None if request fails
        """
        if not self.access_token:
            logger.error("❌ Not authenticated. Please login first.")
            return None
        
        try:
            url = f"{self.base_url}/protected-resource/"
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"✅ Protected resource retrieved")
            return result
            
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Failed to retrieve protected resource: {e}")
            return None
    
    def get_system_status(self) -> Optional[Dict[str, Any]]:
        """
        Get system status (no authentication required).
        
        Returns:
            System status data or None if request fails
        """
        try:
            url = f"{self.base_url}/status"
            response = requests.get(url)
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"✅ System status retrieved")
            return result
            
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Failed to retrieve system status: {e}")
            return None
    
    def get_health(self) -> Optional[Dict[str, Any]]:
        """
        Get health check status (no authentication required).
        
        Returns:
            Health status data or None if request fails
        """
        try:
            url = f"{self.base_url}/health"
            response = requests.get(url)
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"✅ Health check passed")
            return result
            
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Health check failed: {e}")
            return None
    
    def get_admin_logs(self) -> Optional[Dict[str, Any]]:
        """
        Get authentication logs (admin only).
        
        Returns:
            Logs data or None if request fails or not authorized
        """
        if not self.access_token:
            logger.error("❌ Not authenticated. Please login first.")
            return None
        
        try:
            url = f"{self.base_url}/admin/logs"
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"✅ Admin logs retrieved")
            return result
            
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Failed to retrieve admin logs: {e}")
            return None
    
    def get_admin_stats(self) -> Optional[Dict[str, Any]]:
        """
        Get system statistics (admin only).
        
        Returns:
            Stats data or None if request fails or not authorized
        """
        if not self.access_token:
            logger.error("❌ Not authenticated. Please login first.")
            return None
        
        try:
            url = f"{self.base_url}/admin/stats"
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"✅ Admin stats retrieved")
            return result
            
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Failed to retrieve admin stats: {e}")
            return None


def print_section(title: str):
    """Print a formatted section header"""
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70)


def print_json(data: Dict[str, Any]):
    """Pretty print JSON data"""
    print(json.dumps(data, indent=2))


# ============================================================================
# DEMO WORKFLOW
# ============================================================================

def run_demo():
    """Run a complete demo workflow"""
    
    print_section("Valhalla Authentication Service - Client Demo")
    
    # Initialize client
    client = ValhallAuthClient(BASE_URL)
    
    # Step 1: Health Check
    print_section("Step 1: Health Check")
    health = client.get_health()
    if health:
        print_json(health)
    
    # Step 2: System Status
    print_section("Step 2: System Status")
    status = client.get_system_status()
    if status:
        print_json(status)
    
    # Step 3: Login
    print_section("Step 3: Authentication Login")
    logger.info(f"Attempting to login with username: '{USERNAME}'")
    if not client.login(USERNAME, PASSWORD):
        logger.error("❌ Authentication failed. Exiting demo.")
        return
    
    logger.info("✅ Authentication successful!")
    logger.info(f"   Access Token: {client.access_token[:50]}...")
    logger.info(f"   Refresh Token: {client.refresh_token[:50]}...")
    
    # Step 4: Get Secure Data
    print_section("Step 4: Access Protected Endpoint - Secure Data")
    secure_data = client.get_secure_data()
    if secure_data:
        print_json(secure_data)
    
    # Step 5: Get User Profile
    print_section("Step 5: Access Protected Endpoint - User Profile")
    profile = client.get_user_profile()
    if profile:
        print_json(profile)
    
    # Step 6: Get Protected Resource
    print_section("Step 6: Access Protected Endpoint - Protected Resource")
    resource = client.get_protected_resource()
    if resource:
        print_json(resource)
    
    # Step 7: Get Admin Statistics
    print_section("Step 7: Admin Access - System Statistics")
    stats = client.get_admin_stats()
    if stats:
        print_json(stats)
    
    # Step 8: Get Admin Logs
    print_section("Step 8: Admin Access - Authentication Logs")
    logs = client.get_admin_logs()
    if logs:
        logger.info(f"✅ Retrieved {logs.get('total_lines', 0)} log entries")
        print("Last 5 log entries:")
        for log in logs.get('logs', [])[-5:]:
            print(f"  {log.strip()}")
    
    # Step 9: Refresh Token
    print_section("Step 9: Refresh Access Token")
    logger.info("Waiting 2 seconds before refresh...")
    time.sleep(2)
    if client.refresh_access_token():
        logger.info("✅ Token refresh successful!")
        logger.info(f"   New Access Token: {client.access_token[:50]}...")
    
    print_section("Demo Complete")
    logger.info("✅ All tests completed successfully!")
    logger.info("🔐 Authentication service is operational and secure.")


if __name__ == "__main__":
    print("\n🚀 Starting Valhalla Authentication Client Demo...")
    try:
        run_demo()
    except KeyboardInterrupt:
        logger.info("\n⚠️  Demo interrupted by user")
    except Exception as e:
        logger.error(f"❌ Demo error: {e}")
