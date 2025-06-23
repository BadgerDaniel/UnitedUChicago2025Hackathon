#!/usr/bin/env python3
"""
Start the Multi-Agent System with UI
This script starts all agents and then launches the web UI
"""

import subprocess
import time
import os
import sys
import signal
import socket
from pathlib import Path

# Agent configurations - Orchestrator starts last
AGENTS = [
    {"name": "WebScrapingAgent", "port": 10002, "module": "agents.web_scraping_agent"},
    {"name": "GreetingAgent", "port": 10003, "module": "agents.greeting_agent"},
    {"name": "LiveEventsAgent", "port": 10004, "module": "agents.live_events_agent"},
    {"name": "AviationWeatherAgent", "port": 10005, "module": "agents.aviation_weather_agent"},
    {"name": "EconomicIndicatorsAgent", "port": 10006, "module": "agents.economic_indicators_agent"},
    {"name": "GoogleNewsAgent", "port": 10007, "module": "agents.google_news_agent"},
    {"name": "FlightAgent", "port": 10008, "module": "agents.flight_agent"},
    {"name": "HostOrchestrator", "port": 10000, "module": "agents.host_agent.entry"}  # Start last
]

# Colors for terminal output
BLUE = '\033[94m'
GREEN = '\033[92m'
YELLOW = '\033[93m'
RED = '\033[91m'
RESET = '\033[0m'
BOLD = '\033[1m'

# Global list to track processes
processes = []
ui_process = None

def print_header():
    """Print the application header."""
    print(f"\n{BLUE}{BOLD}{'='*60}")
    print(f"   United Airlines Flight Demand Intelligence System")
    print(f"   Multi-Agent Architecture with Web UI")
    print(f"{'='*60}{RESET}\n")

def print_status(message, status="INFO"):
    """Print a status message with color."""
    colors = {
        "INFO": BLUE,
        "SUCCESS": GREEN,
        "WARNING": YELLOW,
        "ERROR": RED
    }
    color = colors.get(status, BLUE)
    print(f"{color}[{status}]{RESET} {message}")

def check_port(port):
    """Check if a port is already in use."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.bind(('localhost', port))
        sock.close()
        return False  # Port is available
    except OSError:
        return True  # Port is in use

def kill_process_on_port(port):
    """Kill any process using the given port."""
    try:
        # Use lsof to find the process using the port
        result = subprocess.run(
            ["lsof", "-ti", f":{port}"],
            capture_output=True,
            text=True
        )
        
        if result.stdout.strip():
            # Get the PID(s)
            pids = result.stdout.strip().split('\n')
            for pid in pids:
                if pid:
                    # Kill the process
                    subprocess.run(["kill", "-9", pid])
                    print_status(f"Killed process {pid} on port {port}", "WARNING")
                    time.sleep(0.5)  # Give it time to release the port
            return True
        return False
    except Exception as e:
        print_status(f"Could not kill process on port {port}: {e}", "WARNING")
        return False

def start_agent(agent):
    """Start a single agent."""
    # Kill any existing process on this port first
    if check_port(agent["port"]):
        print_status(f"Port {agent['port']} is in use, killing existing process...", "WARNING")
        kill_process_on_port(agent["port"])
        time.sleep(1)  # Give it time to fully release
    
    print_status(f"Starting {agent['name']} on port {agent['port']}...")
    
    try:
        process = subprocess.Popen(
            [sys.executable, "-m", agent["module"], "--host", "localhost", "--port", str(agent["port"])],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        
        # Give the agent time to start
        time.sleep(2)
        
        # Check if process is still running
        if process.poll() is None:
            print_status(f"{agent['name']} started successfully", "SUCCESS")
            return process
        else:
            print_status(f"{agent['name']} failed to start", "ERROR")
            return None
            
    except Exception as e:
        print_status(f"Error starting {agent['name']}: {e}", "ERROR")
        return None

def start_ui():
    """Start the web UI."""
    print_status("Starting Web UI...")
    
    # Change to project directory
    project_dir = Path(__file__).parent / "project"
    
    try:
        # Install dependencies if needed
        if not (project_dir / "node_modules").exists():
            print_status("Installing UI dependencies...")
            subprocess.run(["npm", "install"], cwd=project_dir, check=True)
        
        # Start the UI
        process = subprocess.Popen(
            ["npm", "run", "dev"],
            cwd=project_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Wait for the UI to start and capture the URL
        for line in process.stdout:
            if "Local:" in line:
                url = line.strip().split("Local:")[1].strip()
                print_status(f"Web UI started at {url}", "SUCCESS")
                print(f"\n{GREEN}{BOLD}✨ Open your browser at: {url}{RESET}")
                break
        
        return process
        
    except Exception as e:
        print_status(f"Error starting UI: {e}", "ERROR")
        return None

def cleanup(signum=None, frame=None):
    """Clean up all processes."""
    print_status("\nShutting down...", "WARNING")
    
    # Stop UI first
    if ui_process:
        try:
            ui_process.terminate()
            ui_process.wait(timeout=5)
        except:
            ui_process.kill()
    
    # Stop all agents
    for process in processes:
        if process and process.poll() is None:
            try:
                process.terminate()
                process.wait(timeout=5)
            except:
                process.kill()
    
    print_status("All services stopped", "SUCCESS")
    sys.exit(0)

def kill_all_agent_ports():
    """Kill all processes on agent ports before starting."""
    print_status("Cleaning up existing processes on agent ports...", "INFO")
    ports_to_kill = [agent["port"] for agent in AGENTS]
    
    for port in ports_to_kill:
        if check_port(port):
            kill_process_on_port(port)
    
    # Also kill common UI port
    if check_port(5173):
        print_status("Killing process on UI port 5173...", "WARNING")
        kill_process_on_port(5173)
    
    print_status("Port cleanup complete", "SUCCESS")
    time.sleep(2)  # Give time for all ports to be fully released

def main():
    """Main function to start all services."""
    # Set up signal handlers
    signal.signal(signal.SIGINT, cleanup)
    signal.signal(signal.SIGTERM, cleanup)
    
    # Print header
    print_header()
    
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    # Kill all existing processes on agent ports
    kill_all_agent_ports()
    
    # Start agents
    print_status("Starting Agent System...\n")
    
    # Separate orchestrator from other agents
    orchestrator = None
    other_agents = []
    
    for agent in AGENTS:
        if agent["name"] == "HostOrchestrator":
            orchestrator = agent
        else:
            other_agents.append(agent)
    
    # Start all non-orchestrator agents at once
    print_status("Starting specialized agents...")
    for agent in other_agents:
        process = start_agent(agent)
        if process:
            processes.append(process)
    
    # Wait for all agents to initialize
    print_status("Waiting for agents to initialize...")
    time.sleep(5)
    
    # Now start the orchestrator last
    if orchestrator:
        print_status("\nStarting HostOrchestrator (last)...")
        process = start_agent(orchestrator)
        if process:
            processes.append(process)
            print_status("Orchestrator started - it will now discover other agents", "SUCCESS")
        else:
            print_status("Failed to start Orchestrator", "ERROR")
    
    # Check how many agents started successfully
    running_agents = len([p for p in processes if p is not None])
    print_status(f"\n{running_agents}/{len(AGENTS)} agents started successfully\n")
    
    if running_agents == 0:
        print_status("No agents started. Exiting...", "ERROR")
        sys.exit(1)
    
    # Give orchestrator time to discover agents
    time.sleep(3)
    
    # Start UI
    global ui_process
    ui_process = start_ui()
    
    if not ui_process:
        print_status("Failed to start UI", "ERROR")
        cleanup()
    
    # Instructions
    print(f"\n{YELLOW}{BOLD}Instructions:{RESET}")
    print(f"  • The UI should open automatically in your browser")
    print(f"  • If not, navigate to the URL shown above")
    print(f"  • Password: 12345")
    print(f"  • Press Ctrl+C to stop all services\n")
    
    print_status("System is running. Press Ctrl+C to stop.", "INFO")
    
    # Keep the main process running
    try:
        while True:
            # Check if UI is still running
            if ui_process and ui_process.poll() is not None:
                print_status("UI has stopped. Shutting down...", "WARNING")
                cleanup()
            
            # Check agent health periodically
            time.sleep(10)
            
    except KeyboardInterrupt:
        cleanup()

if __name__ == "__main__":
    main()