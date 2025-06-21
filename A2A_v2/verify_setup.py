"""
Setup Verification Script for A2A_v2 Enhanced Travel Analysis System
"""

import os
import sys
import subprocess
from pathlib import Path

def check_file_structure():
    """Verify that all required files are in place."""
    print("🔍 Checking file structure...")
    
    required_files = [
        "requirements.txt",
        "README.md", 
        ".env.example",
        "agents/__init__.py",
        "agents/weather_agent.py",
        "agents/event_agent.py", 
        "agents/flight_agent.py",
        "agents/orchestrator_agent.py",
        "mcp_server/travel_mcp_server.py",
        "travel_agent/travel_analysis_agent.py",
        "travel_agent/main.py",
        "travel_agent/task_manager.py",
        "scripts/start.sh",
        "scripts/stop.sh",
        "tests/test_real_apis.py",
        "tests/demo.py"
    ]
    
    missing_files = []
    for file_path in required_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)
        else:
            print(f"   ✅ {file_path}")
    
    if missing_files:
        print(f"\n❌ Missing files:")
        for file_path in missing_files:
            print(f"   ❌ {file_path}")
        return False
    
    print(f"\n✅ All {len(required_files)} required files present")
    return True

def check_environment():
    """Check environment setup."""
    print("\n🔧 Checking environment...")
    
    # Check Python version
    python_version = sys.version_info
    if python_version.major == 3 and python_version.minor >= 8:
        print(f"   ✅ Python {python_version.major}.{python_version.minor}.{python_version.micro}")
    else:
        print(f"   ❌ Python version {python_version.major}.{python_version.minor} - need 3.8+")
        return False
    
    # Check if in virtual environment
    if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("   ✅ Virtual environment activated")
    else:
        print("   ⚠️  Not in virtual environment (recommended)")
    
    # Check for .env file
    if Path(".env").exists():
        print("   ✅ .env file exists")
        
        # Check for required API keys
        with open(".env", "r") as f:
            env_content = f.read()
        
        if "OPENAI_API_KEY=sk-" in env_content:
            print("   ✅ OpenAI API key configured")
        else:
            print("   ❌ OpenAI API key not configured in .env")
            return False
            
        if "TICKETMASTER_API_KEY" in env_content and not "your_ticketmaster" in env_content:
            print("   ✅ Ticketmaster API key configured")
        else:
            print("   ⚠️  Ticketmaster API key not configured (will use fallback data)")
    else:
        print("   ❌ .env file missing - copy from .env.example")
        return False
    
    return True

def check_dependencies():
    """Check if required dependencies are installed."""
    print("\n📦 Checking dependencies...")
    
    # Updated package mapping with correct import names
    required_packages = [
        ("google-a2a", "google_a2a"),
        ("langchain-openai", "langchain_openai"), 
        ("langchain-core", "langchain_core"),
        ("langgraph", "langgraph"),
        ("langchain-mcp-adapters", "langchain_mcp_adapters"),
        ("mcp", "mcp"),
        ("httpx", "httpx"),
        ("requests", "requests"),
        ("python-dotenv", "dotenv"),  # Fixed: dotenv not python_dotenv
        ("pydantic", "pydantic"),
        ("fastapi", "fastapi"),
        ("uvicorn", "uvicorn")
    ]
    
    missing_packages = []
    
    for package_name, import_name in required_packages:
        try:
            __import__(import_name)
            print(f"   ✅ {package_name}")
        except ImportError:
            missing_packages.append(package_name)
            print(f"   ❌ {package_name}")
    
    if missing_packages:
        print(f"\n❌ Missing packages: {', '.join(missing_packages)}")
        print("Install with: pip install -r requirements.txt")
        return False
    
    print(f"\n✅ All {len(required_packages)} required packages installed")
    return True

def check_script_permissions():
    """Check if scripts are executable."""
    print("\n🔐 Checking script permissions...")
    
    scripts = ["scripts/start.sh", "scripts/stop.sh"]
    
    for script in scripts:
        if Path(script).exists():
            if os.access(script, os.X_OK):
                print(f"   ✅ {script} is executable")
            else:
                print(f"   ⚠️  {script} not executable - run: chmod +x {script}")
        else:
            print(f"   ❌ {script} missing")
    
    return True

def check_ports():
    """Check if required ports are available."""
    print("\n🔌 Checking port availability...")
    
    required_ports = [8000, 10001]
    
    for port in required_ports:
        try:
            result = subprocess.run(['lsof', '-i', f':{port}'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                print(f"   ⚠️  Port {port} is in use")
            else:
                print(f"   ✅ Port {port} available")
        except FileNotFoundError:
            print(f"   ⚠️  Cannot check port {port} (lsof not available)")
    
    return True

def provide_setup_instructions():
    """Provide setup instructions based on findings."""
    print("\n📋 SETUP INSTRUCTIONS")
    print("=" * 40)
    
    print("\n1. 🐍 Python Environment:")
    print("   python -m venv venv")
    print("   source venv/bin/activate  # Windows: venv\\Scripts\\activate")
    
    print("\n2. 📦 Install Dependencies:")
    print("   pip install -r requirements.txt")
    
    print("\n3. 🔑 Configure API Keys:")
    print("   cp .env.example .env")
    print("   # Edit .env and add your API keys:")
    print("   # OPENAI_API_KEY=sk-your_key_here")
    print("   # TICKETMASTER_API_KEY=your_key_here (optional)")
    
    print("\n4. 🔐 Make Scripts Executable:")
    print("   chmod +x scripts/*.sh")
    
    print("\n5. 🚀 Start System:")
    print("   ./scripts/start.sh")
    
    print("\n6. 🧪 Test System:")
    print("   python tests/test_real_apis.py")
    print("   python tests/demo.py")

def run_verification():
    """Run complete system verification."""
    print("🔍 A2A_v2 ENHANCED TRAVEL ANALYSIS SYSTEM VERIFICATION")
    print("=" * 65)
    
    checks = [
        ("File Structure", check_file_structure),
        ("Environment", check_environment), 
        ("Dependencies", check_dependencies),
        ("Script Permissions", check_script_permissions),
        ("Port Availability", check_ports)
    ]
    
    results = {}
    
    for check_name, check_func in checks:
        try:
            results[check_name] = check_func()
        except Exception as e:
            print(f"   ❌ Error in {check_name}: {e}")
            results[check_name] = False
    
    # Summary
    print(f"\n📊 VERIFICATION SUMMARY")
    print("=" * 30)
    
    passed = sum(results.values())
    total = len(results)
    
    for check_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {check_name}: {status}")
    
    print(f"\n🎯 Overall: {passed}/{total} checks passed")
    
    if passed == total:
        print("\n🎉 SYSTEM VERIFICATION SUCCESSFUL!")
        print("✅ Your A2A_v2 system is ready to run")
        print("\n🚀 Next steps:")
        print("   1. ./scripts/start.sh")
        print("   2. python tests/demo.py")
        print("   3. Connect your A2A client to http://localhost:10001")
        
    elif passed >= 3:
        print("\n⚠️  PARTIAL SUCCESS - System should work with limitations")
        print("Address failed checks above for full functionality")
        
    else:
        print("\n❌ VERIFICATION FAILED")
        print("Please address the issues above before proceeding")
        provide_setup_instructions()
    
    return passed == total

if __name__ == "__main__":
    success = run_verification()
    
    if not success:
        print(f"\n📖 For detailed setup instructions, see:")
        print("   • README.md")
        print("   • docs/SETUP.md (if available)")
        
    sys.exit(0 if success else 1)
