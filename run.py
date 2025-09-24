#!/usr/bin/env python3
"""
DLD to Cursor AI Prompt Generation System
Quick start script with various operation modes
"""

import sys
import os
import argparse
import asyncio
import subprocess
from pathlib import Path

def check_requirements():
    """Check if all requirements are met"""
    print("🔍 Checking requirements...")
    
    # Check Python version
    if sys.version_info < (3, 11):
        print("❌ Python 3.11+ required")
        return False
    print("✅ Python version OK")
    
    # Check if requirements.txt exists
    if not Path("requirements.txt").exists():
        print("❌ requirements.txt not found")
        return False
    print("✅ requirements.txt found")
    
    # Check if OpenAI API key is set
    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️  OPENAI_API_KEY not set (you can set it later)")
    else:
        print("✅ OPENAI_API_KEY configured")
    
    return True

def install_dependencies():
    """Install Python dependencies"""
    print("📦 Installing dependencies...")
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], 
                      check=True, capture_output=True, text=True)
        print("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        print(f"Error output: {e.stderr}")
        return False

def setup_environment():
    """Set up the environment"""
    print("🔧 Setting up environment...")
    
    # Create necessary directories
    directories = ["knowledge_base/data", "logs", "output"]
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"📁 Created directory: {directory}")
    
    # Copy example environment file if .env doesn't exist
    if not Path(".env").exists() and Path("env.example").exists():
        import shutil
        shutil.copy("env.example", ".env")
        print("📄 Created .env from env.example")
        print("⚠️  Please edit .env and add your OpenAI API key")
    
    print("✅ Environment setup complete")

def run_server(host="0.0.0.0", port=8000, reload=False):
    """Run the FastAPI server"""
    print(f"🚀 Starting server on http://{host}:{port}")
    
    try:
        import uvicorn
        
        # Run the server
        uvicorn.run(
            "main:app",
            host=host,
            port=port,
            reload=reload,
            log_level="info"
        )
    except ImportError:
        print("❌ uvicorn not installed. Installing...")
        subprocess.run([sys.executable, "-m", "pip", "install", "uvicorn"], check=True)
        import uvicorn
        uvicorn.run("main:app", host=host, port=port, reload=reload)
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except Exception as e:
        print(f"❌ Server error: {e}")

def run_examples():
    """Run usage examples"""
    print("📚 Running usage examples...")
    
    if not Path("examples/usage_examples.py").exists():
        print("❌ Usage examples not found")
        return
    
    try:
        subprocess.run([sys.executable, "examples/usage_examples.py"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Examples failed: {e}")
    except KeyboardInterrupt:
        print("\n🛑 Examples stopped by user")

def run_tests():
    """Run tests if available"""
    print("🧪 Running tests...")
    
    # Check if pytest is available
    try:
        import pytest
        # Run tests
        subprocess.run([sys.executable, "-m", "pytest", "-v"], check=True)
    except ImportError:
        print("📦 Installing pytest...")
        subprocess.run([sys.executable, "-m", "pip", "install", "pytest"], check=True)
        subprocess.run([sys.executable, "-m", "pytest", "-v"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Tests failed: {e}")

def docker_build():
    """Build Docker image"""
    print("🐳 Building Docker image...")
    
    try:
        subprocess.run(["docker", "build", "-t", "dld-prompt-generator", "."], check=True)
        print("✅ Docker image built successfully")
    except subprocess.CalledProcessError as e:
        print(f"❌ Docker build failed: {e}")
    except FileNotFoundError:
        print("❌ Docker not found. Please install Docker first.")

def docker_run():
    """Run with Docker Compose"""
    print("🐳 Starting with Docker Compose...")
    
    try:
        subprocess.run(["docker-compose", "up", "-d"], check=True)
        print("✅ Docker containers started")
        print("🌐 Server available at http://localhost:8000")
        print("📊 Health check: http://localhost:8000/health")
    except subprocess.CalledProcessError as e:
        print(f"❌ Docker Compose failed: {e}")
    except FileNotFoundError:
        print("❌ Docker Compose not found. Please install Docker Compose first.")

def docker_stop():
    """Stop Docker containers"""
    print("🐳 Stopping Docker containers...")
    
    try:
        subprocess.run(["docker-compose", "down"], check=True)
        print("✅ Docker containers stopped")
    except subprocess.CalledProcessError as e:
        print(f"❌ Docker stop failed: {e}")

def show_status():
    """Show system status"""
    print("📊 System Status")
    print("=" * 50)
    
    # Check if server is running
    try:
        import requests
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            health_data = response.json()
            print("🟢 Server: Running")
            print(f"   System initialized: {health_data.get('system_initialized', False)}")
            print(f"   Knowledge base ready: {health_data.get('knowledge_base_ready', False)}")
        else:
            print("🔴 Server: Not responding properly")
    except:
        print("🔴 Server: Not running")
    
    # Check Docker containers
    try:
        result = subprocess.run(["docker-compose", "ps"], capture_output=True, text=True)
        if "dld-prompt-generator" in result.stdout:
            if "Up" in result.stdout:
                print("🟢 Docker: Running")
            else:
                print("🔴 Docker: Stopped")
        else:
            print("⚪ Docker: Not deployed")
    except:
        print("⚪ Docker: Not available")
    
    # Check configuration
    if Path(".env").exists():
        print("🟢 Configuration: .env file exists")
    else:
        print("🔴 Configuration: .env file missing")
    
    # Check knowledge base
    kb_path = Path("knowledge_base/data")
    if kb_path.exists() and any(kb_path.iterdir()):
        print("🟢 Knowledge Base: Initialized")
    else:
        print("⚪ Knowledge Base: Empty")

def interactive_setup():
    """Interactive setup wizard"""
    print("🧙‍♂️ DLD to Cursor AI Prompt Generator - Setup Wizard")
    print("=" * 60)
    
    if not check_requirements():
        print("❌ Requirements check failed. Please fix the issues above.")
        return
    
    # Ask about installation
    install = input("📦 Install/update dependencies? (y/N): ").lower().startswith('y')
    if install:
        if not install_dependencies():
            return
    
    # Setup environment
    setup_env = input("🔧 Set up environment directories? (Y/n): ").lower()
    if setup_env != 'n':
        setup_environment()
    
    # Ask about OpenAI API key
    if not os.getenv("OPENAI_API_KEY"):
        api_key = input("🔑 Enter OpenAI API key (optional, press Enter to skip): ").strip()
        if api_key:
            # Write to .env file
            with open(".env", "a") as f:
                f.write(f"\nOPENAI_API_KEY={api_key}\n")
            print("✅ API key saved to .env file")
    
    # Ask about running method
    print("\n🚀 How would you like to run the system?")
    print("1. Local Python server (development)")
    print("2. Docker Compose (production)")
    print("3. Just setup, don't run")
    
    choice = input("Choose option (1/2/3): ").strip()
    
    if choice == "1":
        reload = input("🔄 Enable auto-reload for development? (y/N): ").lower().startswith('y')
        run_server(reload=reload)
    elif choice == "2":
        docker_run()
    else:
        print("✅ Setup complete! You can now run the system manually.")
        print("\nQuick start commands:")
        print("  Local server: python run.py --server")
        print("  Docker:       python run.py --docker")
        print("  Examples:     python run.py --examples")

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="DLD to Cursor AI Prompt Generation System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run.py --setup          # Interactive setup wizard
  python run.py --server         # Run local development server
  python run.py --docker         # Run with Docker Compose
  python run.py --examples       # Run usage examples
  python run.py --test           # Run tests
  python run.py --status         # Show system status
        """
    )
    
    # Add arguments
    parser.add_argument("--setup", action="store_true", help="Run interactive setup wizard")
    parser.add_argument("--server", action="store_true", help="Run local development server")
    parser.add_argument("--docker", action="store_true", help="Run with Docker Compose")
    parser.add_argument("--docker-build", action="store_true", help="Build Docker image")
    parser.add_argument("--docker-stop", action="store_true", help="Stop Docker containers")
    parser.add_argument("--examples", action="store_true", help="Run usage examples")
    parser.add_argument("--test", action="store_true", help="Run tests")
    parser.add_argument("--status", action="store_true", help="Show system status")
    parser.add_argument("--install", action="store_true", help="Install dependencies")
    parser.add_argument("--host", default="0.0.0.0", help="Server host (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=8000, help="Server port (default: 8000)")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload for development")
    
    args = parser.parse_args()
    
    # If no arguments provided, run interactive setup
    if not any(vars(args).values()):
        interactive_setup()
        return
    
    # Handle different commands
    if args.setup:
        interactive_setup()
    elif args.install:
        install_dependencies()
    elif args.server:
        if not check_requirements():
            return
        run_server(host=args.host, port=args.port, reload=args.reload)
    elif args.docker_build:
        docker_build()
    elif args.docker:
        docker_run()
    elif args.docker_stop:
        docker_stop()
    elif args.examples:
        run_examples()
    elif args.test:
        run_tests()
    elif args.status:
        show_status()
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
