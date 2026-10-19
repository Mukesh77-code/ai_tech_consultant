"""
Unified Launcher for AI Tech Consultant.
Starts Task 1 Knowledge Brain API (port 8000) and Task 2 Inbox Agent (port 3000) concurrently.
"""

import os
import subprocess
import sys
import time
import webbrowser

def main():
    root_dir = os.path.abspath(os.path.dirname(__file__))
    print("=" * 80)
    print("STARTING AI TECH CONSULTANT ENTERPRISE SUITE")
    print("=" * 80)
    print("1. Task 1: Knowledge Brain API      -> http://127.0.0.1:8000/docs")
    print("2. Task 2: Inbox Agent Web UI       -> http://localhost:3000")
    print("3. Task 3: Meeting to Scope Engine  -> Ready (Python CLI / Orchestrator)")
    print("=" * 80)

    # 1. Start Task 1 Knowledge Brain (FastAPI / Uvicorn)
    venv_py = os.path.join(root_dir, ".venv", "Scripts", "python.exe")
    py_exec = venv_py if os.path.exists(venv_py) else sys.executable
    t1_cmd = [py_exec, "-m", "uvicorn", "task1_knowledge_brain.api.app:app", "--host", "127.0.0.1", "--port", "8000"]
    print("\n[Launcher] Booting Task 1 Knowledge Brain API...")
    p1 = subprocess.Popen(t1_cmd, cwd=root_dir)

    # 2. Start Task 2 Inbox Agent (Node.js / Express)
    t2_dir = os.path.join(root_dir, "task2_inbox_agent")
    t2_cmd = ["node", "dist/server.js"]
    print("[Launcher] Booting Task 2 Inbox Agent Server...")
    p2 = subprocess.Popen(t2_cmd, cwd=t2_dir, shell=True)

    print("\n[Launcher] All services active. Opening Inbox Agent Web UI in browser...")
    time.sleep(2)
    try:
        webbrowser.open("http://localhost:3000")
    except Exception:
        pass

    print("\nPress Ctrl+C to terminate all services.")
    try:
        p1.wait()
        p2.wait()
    except KeyboardInterrupt:
        print("\nShutting down services...")
        p1.terminate()
        p2.terminate()
        p1.wait()
        p2.wait()
        print("Done.")

if __name__ == "__main__":
    main()
