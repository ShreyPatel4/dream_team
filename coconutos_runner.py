import multiprocessing
import subprocess
import time
import os
import sys

def run_service(script_name):
    """Execution wrapper for background Python services."""
    project_root = os.path.dirname(os.path.abspath(__file__))
    script_path = os.path.join(project_root, script_name)
    
    print(f"[*] Starting {script_name}...")
    try:
        # Use sys.executable to ensure we use the same Python environment
        subprocess.run([sys.executable, script_path], check=True)
    except subprocess.CalledProcessError as e:
        print(f"[!] {script_name} crashed with exit code {e.returncode}. Restarting in 5s...")
        time.sleep(5)
        run_service(script_name)
    except Exception as e:
        print(f"[!] {script_name} failed: {e}")

if __name__ == "__main__":
    print("-" * 40)
    print("🚀 CoconutOS Dream Team v4.3 - Universal Runner")
    print("-" * 40)
    print(f"OS Detected: {sys.platform}")
    
    # Define the core microservices
    services = ["slack_listener.py", "agi_orchestrator.py"]
    
    processes = []
    
    for service in services:
        p = multiprocessing.Process(target=run_service, args=(service,))
        p.start()
        processes.append(p)
        
    print(f"\n[+] {len(services)} services are now running in the background.")
    print("[+] Press Ctrl+C to shut down the entire cluster.\n")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[!] Shutdown signal received. Killing all agents...")
        for p in processes:
            p.terminate()
        print("[v] Cluster stopped successfully.")
