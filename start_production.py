"""
Production Entrypoint for AI Tech Consultant Container.
Launches:
1. Task 1 Knowledge Brain FastAPI on internal port (default 8000)
2. Task 2 Inbox Agent Express Server on public $PORT (default 3000)
Handles graceful shutdown on SIGTERM/SIGINT.
"""

import os
import signal
import subprocess
import sys
import time

def main():
    root_dir = os.path.abspath(os.path.dirname(__file__))
    public_port = os.getenv("PORT", "3000")
    internal_kb_port = os.getenv("KNOWLEDGE_BRAIN_PORT", "8000")

    print("=" * 80)
    print("STARTING AI TECH CONSULTANT ENTERPRISE SUITE (PRODUCTION)")
    print(f"Public Web UI Port:           {public_port}")
    print(f"Internal Knowledge Brain Port: {internal_kb_port}")
    print("=" * 80)

    # 1. Start Task 1 Knowledge Brain (FastAPI / Uvicorn)
    t1_cmd = [
        sys.executable, "-m", "uvicorn",
        "task1_knowledge_brain.api.app:app",
        "--host", "0.0.0.0",
        "--port", str(internal_kb_port)
    ]
    print("[Production Launcher] Booting Task 1 Knowledge Brain API...")
    p1 = subprocess.Popen(t1_cmd, cwd=root_dir)

    # Allow Task 1 to complete startup
    time.sleep(2)

    # 2. Start Task 2 Inbox Agent (Node.js / Express)
    t2_dir = os.path.join(root_dir, "task2_inbox_agent")
    env = dict(
        os.environ,
        PORT=str(public_port),
        KNOWLEDGE_BRAIN_URL=f"http://127.0.0.1:{internal_kb_port}"
    )
    print("[Production Launcher] Booting Task 2 Inbox Agent Server...")
    p2 = subprocess.Popen(["node", "dist/server.js"], cwd=t2_dir, env=env)

    def shutdown(signum, frame):
        print("\n[Production Launcher] Termination signal received. Shutting down gracefully...")
        p1.terminate()
        p2.terminate()
        p1.wait()
        p2.wait()
        print("[Production Launcher] All services stopped.")
        sys.exit(0)

    signal.signal(signal.SIGTERM, shutdown)
    signal.signal(signal.SIGINT, shutdown)

    print("[Production Launcher] All services active.")
    try:
        while True:
            code1 = p1.poll()
            code2 = p2.poll()
            if code1 is not None or code2 is not None:
                print(f"[Production Launcher] Process terminated (Task 1: {code1}, Task 2: {code2}). Exiting...")
                p1.terminate()
                p2.terminate()
                break
            time.sleep(1)
    except KeyboardInterrupt:
        shutdown(None, None)

if __name__ == "__main__":
    main()
