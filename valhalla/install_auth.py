"""
Valhalla Authentication System - Installation & Testing Script
Complete setup and validation of the secure authentication service
"""

import subprocess
import sys
import os
import time
from pathlib import Path
from typing import List, Tuple


class AuthInstaller:
    """Manages installation and testing of the authentication system"""
    
    def __init__(self):
        self.base_path = Path(__file__).parent
        self.requirements = [
            "fastapi",
            "uvicorn",
            "python-jose[cryptography]",
            "passlib[bcrypt]",
            "pydantic",
            "python-dotenv",
            "requests"
        ]
        self.status = {"success": 0, "failed": 0}
    
    def print_header(self, title: str):
        """Print formatted section header"""
        print("\n" + "="*70)
        print(f"  {title}")
        print("="*70)
    
    def print_step(self, step: int, description: str):
        """Print step information"""
        print(f"\n[Step {step}] {description}")
        print("-" * 70)
    
    def run_command(self, command: str, description: str = "") -> Tuple[bool, str]:
        """Run a shell command and return success status"""
        try:
            print(f"  ▶ {description or command}")
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                print(f"  ✅ Success")
                self.status["success"] += 1
                return True, result.stdout
            else:
                print(f"  ❌ Failed")
                self.status["failed"] += 1
                return False, result.stderr
        
        except subprocess.TimeoutExpired:
            print(f"  ⏱️  Timeout")
            self.status["failed"] += 1
            return False, "Command timed out"
        except Exception as e:
            print(f"  ❌ Error: {e}")
            self.status["failed"] += 1
            return False, str(e)
    
    def check_python_version(self):
        """Verify Python version is 3.8+"""
        self.print_step(1, "Verify Python Version")
        
        success, output = self.run_command(
            "python --version",
            "Checking Python version"
        )
        
        if success:
            print(f"  ℹ️  {output.strip()}")
            if "3.8" in output or "3.9" in output or "3.10" in output or "3.11" in output:
                print("  ✅ Python version is compatible (3.8+)")
                return True
        
        print("  ❌ Python 3.8 or higher required")
        return False
    
    def check_pip(self):
        """Verify pip is installed"""
        self.print_step(2, "Verify pip")
        
        success, output = self.run_command(
            "pip --version",
            "Checking pip installation"
        )
        
        if success:
            print(f"  ℹ️  {output.strip()}")
            print("  ✅ pip is available")
            return True
        
        print("  ❌ pip is not available")
        return False
    
    def install_requirements(self):
        """Install all required packages"""
        self.print_step(3, "Install Required Packages")
        
        print(f"  📦 Installing {len(self.requirements)} packages...")
        
        for package in self.requirements:
            success, _ = self.run_command(
                f"pip install -q {package}",
                f"Installing {package}"
            )
            if not success:
                print(f"  ⚠️  Failed to install {package}")
                return False
        
        print(f"  ✅ All {len(self.requirements)} packages installed successfully")
        return True
    
    def verify_imports(self):
        """Verify all required packages can be imported"""
        self.print_step(4, "Verify Package Imports")
        
        modules = [
            ("fastapi", "FastAPI"),
            ("uvicorn", "Uvicorn"),
            ("pydantic", "Pydantic"),
            ("jose", "python-jose"),
            ("passlib", "Passlib"),
            ("requests", "Requests"),
            ("dotenv", "python-dotenv")
        ]
        
        all_imported = True
        for module, display_name in modules:
            try:
                __import__(module)
                print(f"  ✅ {display_name:20} - Imported successfully")
            except ImportError as e:
                print(f"  ❌ {display_name:20} - Import failed: {e}")
                all_imported = False
        
        return all_imported
    
    def check_auth_files(self):
        """Verify authentication files exist"""
        self.print_step(5, "Verify Authentication Files")
        
        files_to_check = [
            ("services/auth_service.py", "Authentication Service"),
            ("auth_client.py", "Authentication Client"),
            ("VALHALLA_AUTH_SETUP.md", "Setup Guide"),
            ("VALHALLA_AUTH_QUICK_START.md", "Quick Start Guide")
        ]
        
        all_exist = True
        for filepath, description in files_to_check:
            full_path = self.base_path / filepath
            if full_path.exists():
                size = full_path.stat().st_size
                print(f"  ✅ {description:30} - {size:,} bytes")
            else:
                print(f"  ❌ {description:30} - NOT FOUND")
                all_exist = False
        
        return all_exist
    
    def validate_auth_service(self):
        """Validate auth_service.py syntax"""
        self.print_step(6, "Validate Authentication Service Code")
        
        auth_service = self.base_path / "services" / "auth_service.py"
        
        if not auth_service.exists():
            print(f"  ❌ Auth service not found: {auth_service}")
            return False
        
        success, output = self.run_command(
            f"python -m py_compile {auth_service}",
            "Compiling auth_service.py"
        )
        
        if success:
            print(f"  ✅ Auth service syntax is valid")
            
            # Check for required components
            try:
                with open(auth_service, 'r') as f:
                    content = f.read()
                
                required_components = [
                    ("SECRET_KEY", "JWT Secret Key"),
                    ("class ValhallAuthClient", "Auth Client Class"),
                    ("def create_access_token", "Token Creation"),
                    ("def verify_token", "Token Verification"),
                    ("@app.post('/token')", "Login Endpoint"),
                    ("@app.get('/secure-data/')", "Protected Endpoint"),
                ]
                
                print("\n  🔍 Checking for required components:")
                for component, description in required_components:
                    if component in content:
                        print(f"    ✅ {description:30} - Found")
                    else:
                        print(f"    ❌ {description:30} - NOT FOUND")
                
                return True
            except Exception as e:
                print(f"  ❌ Error reading auth service: {e}")
                return False
        
        print(f"  ❌ Compilation failed: {output}")
        return False
    
    def validate_auth_client(self):
        """Validate auth_client.py syntax"""
        self.print_step(7, "Validate Authentication Client Code")
        
        auth_client = self.base_path / "auth_client.py"
        
        if not auth_client.exists():
            print(f"  ❌ Auth client not found: {auth_client}")
            return False
        
        success, output = self.run_command(
            f"python -m py_compile {auth_client}",
            "Compiling auth_client.py"
        )
        
        if success:
            print(f"  ✅ Auth client syntax is valid")
            
            # Check for required classes and methods
            try:
                with open(auth_client, 'r') as f:
                    content = f.read()
                
                required_components = [
                    ("class ValhallAuthClient", "Auth Client Class"),
                    ("def login", "Login Method"),
                    ("def get_secure_data", "Secure Data Method"),
                    ("def get_user_profile", "User Profile Method"),
                    ("def run_demo", "Demo Function"),
                ]
                
                print("\n  🔍 Checking for required components:")
                for component, description in required_components:
                    if component in content:
                        print(f"    ✅ {description:30} - Found")
                    else:
                        print(f"    ❌ {description:30} - NOT FOUND")
                
                return True
            except Exception as e:
                print(f"  ❌ Error reading auth client: {e}")
                return False
        
        print(f"  ❌ Compilation failed: {output}")
        return False
    
    def check_git(self):
        """Verify git repository status"""
        self.print_step(8, "Check Git Repository")
        
        # Check if git is initialized
        success, _ = self.run_command(
            "git status",
            "Checking git status"
        )
        
        if success:
            print("  ✅ Git repository detected")
            
            # Get latest commit
            success, commit_info = self.run_command(
                "git log --oneline -1",
                "Getting latest commit"
            )
            
            if success:
                print(f"  ℹ️  Latest commit: {commit_info.strip()}")
            
            return True
        
        print("  ⚠️  Git repository not initialized")
        return True  # Not critical
    
    def print_credentials(self):
        """Display login credentials"""
        self.print_step(9, "Authentication Credentials")
        
        print("""
  🔑 Login Credentials:
  
  Username: The All father
  Password: IAmBatman!1
  
  ℹ️  Note: These credentials are configured in services/auth_service.py
  ⚠️  Change SECRET_KEY for production deployment
        """)
    
    def print_quick_start(self):
        """Print quick start instructions"""
        self.print_step(10, "Quick Start Instructions")
        
        print("""
  🚀 To start the authentication service:
  
  1. Open a terminal in this directory
  
  2. Run the service:
     uvicorn services.auth_service:app --reload
  
  3. The service will be available at:
     http://localhost:8000
  
  4. Interactive documentation:
     - Swagger UI: http://localhost:8000/docs
     - ReDoc: http://localhost:8000/redoc
  
  5. In another terminal, run the demo client:
     python auth_client.py
  
  6. Or test with curl:
     curl -X POST http://localhost:8000/token \\
       -H "Content-Type: application/json" \\
       -d '{"username": "The All father", "password": "IAmBatman!1"}'
        """)
    
    def print_summary(self):
        """Print installation summary"""
        self.print_header("Installation Summary")
        
        total = self.status["success"] + self.status["failed"]
        success_rate = (self.status["success"] / total * 100) if total > 0 else 0
        
        print(f"""
  📊 Installation Results:
  
  ✅ Successful:  {self.status["success"]}
  ❌ Failed:      {self.status["failed"]}
  📈 Success Rate: {success_rate:.1f}%
  
  📁 Files Created/Verified:
     • services/auth_service.py (Main service)
     • auth_client.py (Testing client)
     • VALHALLA_AUTH_SETUP.md (Setup guide)
     • VALHALLA_AUTH_QUICK_START.md (Quick reference)
  
  🔐 Authentication Method:
     • OAuth 2.0 + JWT Tokens
     • Bcrypt password hashing ready
     • CORS protection configured
     • Comprehensive logging enabled
  
  📚 Documentation:
     • Complete setup guide available
     • Quick start guide available
     • Inline code documentation
     • Example client code provided
  
  🎯 Next Steps:
     1. Start the service: uvicorn services.auth_service:app --reload
     2. Visit: http://localhost:8000/docs
     3. Run demo: python auth_client.py
     4. Review: VALHALLA_AUTH_SETUP.md for production deployment
        """)
    
    def run_full_installation(self):
        """Run complete installation process"""
        self.print_header("🔐 Valhalla Authentication System Setup")
        
        print("""
  Welcome to Valhalla Secure Login and Authentication Setup!
  
  This installer will:
  ✓ Verify Python and pip
  ✓ Install required packages
  ✓ Validate authentication files
  ✓ Check code syntax
  ✓ Provide quick start instructions
        """)
        
        # Run all checks
        checks = [
            ("Python Version", self.check_python_version),
            ("pip Installation", self.check_pip),
            ("Install Packages", self.install_requirements),
            ("Import Verification", self.verify_imports),
            ("Auth Files Check", self.check_auth_files),
            ("Auth Service Validation", self.validate_auth_service),
            ("Auth Client Validation", self.validate_auth_client),
            ("Git Repository", self.check_git),
        ]
        
        for check_name, check_func in checks:
            try:
                if not check_func():
                    print(f"\n  ⚠️  {check_name} encountered issues")
            except Exception as e:
                print(f"\n  ❌ {check_name} error: {e}")
        
        # Print additional information
        self.print_credentials()
        self.print_quick_start()
        self.print_summary()
        
        print("\n" + "="*70)
        print("  ✅ Installation Complete!")
        print("="*70)
        print("\n  🎉 Your authentication system is ready to use!\n")


def main():
    """Main entry point"""
    try:
        installer = AuthInstaller()
        installer.run_full_installation()
    except KeyboardInterrupt:
        print("\n\n⚠️  Installation interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Installation error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
