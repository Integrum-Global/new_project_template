#!/usr/bin/env python3
"""
Startup script for User Management System servers

This script starts both the API and WebSocket servers for development.
"""

import os
import signal
import subprocess
import sys
import time
from typing import List, Optional

# Colors for output
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BLUE = "\033[94m"
RESET = "\033[0m"


class ServerManager:
    """Manages API and WebSocket server processes"""

    def __init__(self):
        self.processes: List[subprocess.Popen] = []
        self.running = False

    def start_api_server(self, host: str = "0.0.0.0", port: int = 8000):
        """Start the API server"""
        print(f"{BLUE}Starting API Server on {host}:{port}...{RESET}")

        env = os.environ.copy()
        env.update(
            {
                "API_HOST": host,
                "API_PORT": str(port),
                "ENVIRONMENT": "development",
                "DATABASE_URL": "sqlite+aiosqlite:///user_management.db",
                "JWT_SECRET_KEY": "development-secret-key",
                "WORKERS": "1",  # Single worker for development
            }
        )

        cmd = [sys.executable, "workflows/shared/api_server.py"]

        process = subprocess.Popen(
            cmd,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
        )

        self.processes.append(process)
        print(f"{GREEN}✓ API Server started (PID: {process.pid}){RESET}")

        return process

    def start_websocket_server(self, host: str = "0.0.0.0", port: int = 8001):
        """Start the WebSocket server"""
        print(f"{BLUE}Starting WebSocket Server on {host}:{port}...{RESET}")

        env = os.environ.copy()
        env.update(
            {
                "WEBSOCKET_HOST": host,
                "WEBSOCKET_PORT": str(port),
                "ENVIRONMENT": "development",
                "JWT_SECRET_KEY": "development-secret-key",
            }
        )

        cmd = [sys.executable, "workflows/shared/websocket_server.py"]

        process = subprocess.Popen(
            cmd,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
        )

        self.processes.append(process)
        print(f"{GREEN}✓ WebSocket Server started (PID: {process.pid}){RESET}")

        return process

    def monitor_processes(self):
        """Monitor server processes and display logs"""
        print(f"\n{YELLOW}Monitoring server processes...{RESET}")
        print(f"{YELLOW}Press Ctrl+C to stop all servers{RESET}\n")

        try:
            while self.running:
                for process in self.processes:
                    # Check if process is still running
                    if process.poll() is not None:
                        print(f"{RED}Process {process.pid} has stopped!{RESET}")
                        self.running = False
                        break

                    # Read and display any output
                    if process.stdout:
                        line = process.stdout.readline()
                        if line:
                            print(f"[API] {line.strip()}")

                    if process.stderr:
                        line = process.stderr.readline()
                        if line:
                            print(f"[ERROR] {line.strip()}")

                time.sleep(0.1)

        except KeyboardInterrupt:
            print(f"\n{YELLOW}Shutting down servers...{RESET}")

    def stop_all(self):
        """Stop all server processes"""
        for process in self.processes:
            if process.poll() is None:
                print(f"{YELLOW}Stopping process {process.pid}...{RESET}")
                process.terminate()

                # Wait up to 5 seconds for graceful shutdown
                try:
                    process.wait(timeout=5)
                    print(f"{GREEN}✓ Process {process.pid} stopped gracefully{RESET}")
                except subprocess.TimeoutExpired:
                    print(f"{RED}Force killing process {process.pid}...{RESET}")
                    process.kill()
                    process.wait()

        self.processes.clear()
        self.running = False

    def run(self):
        """Run the server manager"""
        self.running = True

        # Register signal handler for clean shutdown
        signal.signal(signal.SIGINT, lambda sig, frame: self.stop_all())
        signal.signal(signal.SIGTERM, lambda sig, frame: self.stop_all())

        print(f"{GREEN}{'='*60}{RESET}")
        print(f"{GREEN}User Management System - Development Servers{RESET}")
        print(f"{GREEN}{'='*60}{RESET}")

        # Start servers
        self.start_api_server()
        time.sleep(2)  # Give API server time to start

        self.start_websocket_server()
        time.sleep(2)  # Give WebSocket server time to start

        print(f"\n{GREEN}All servers started successfully!{RESET}")
        print(f"\n{BLUE}Access Points:{RESET}")
        print("  - API Server: http://localhost:8000")
        print("  - API Documentation: http://localhost:8000/docs")
        print("  - WebSocket Server: ws://localhost:8001")
        print("  - Health Check: http://localhost:8000/health")

        print(f"\n{BLUE}Test the API:{RESET}")
        print("  python test_api.py")

        # Monitor processes
        self.monitor_processes()

        # Cleanup
        self.stop_all()
        print(f"\n{GREEN}All servers stopped.{RESET}")


def check_requirements():
    """Check if required packages are installed"""
    required_packages = [
        "fastapi",
        "uvicorn",
        "httpx",
        "websockets",
        "pydantic",
        "jwt",
        "sqlalchemy",
    ]

    missing_packages = []

    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)

    if missing_packages:
        print(f"{RED}Missing required packages:{RESET}")
        for package in missing_packages:
            print(f"  - {package}")
        print(f"\n{YELLOW}Install missing packages with:{RESET}")
        print(f"  pip install {' '.join(missing_packages)}")
        return False

    return True


def main():
    """Main entry point"""
    # Change to app directory
    app_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(app_dir)

    # Check requirements
    if not check_requirements():
        return 1

    # Create and run server manager
    manager = ServerManager()

    try:
        manager.run()
    except Exception as e:
        print(f"{RED}Error: {str(e)}{RESET}")
        manager.stop_all()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
