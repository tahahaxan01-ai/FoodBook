"""
FoodBook Full-Stack Launcher
============================
Launches:
1. AI/ML Recommendation Service on http://localhost:8001
2. FastAPI Backend & Frontend Single Page Application on http://localhost:8000
"""

import os
import sys
import subprocess
import time
import webbrowser
import threading


def run_ml_service():
    ml_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "ml_service/ml_service"))
    print(f"[*] Starting FoodBook AI/ML Recommendation Service on port 8001 (cwd: {ml_dir})...")
    subprocess.run(
        [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"],
        cwd=ml_dir
    )


def run_backend():
    backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "backend"))
    print(f"[*] Starting FoodBook Backend & SPA on port 8000 (cwd: {backend_dir})...")
    subprocess.run(
        [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"],
        cwd=backend_dir
    )


if __name__ == "__main__":
    sep = "=" * 65
    print(sep)
    print("  FOODBOOK - AI-Powered Personalized Food Discovery")
    print(sep)
    print("  Frontend & Backend API : http://localhost:8000")
    print("  Interactive API Docs   : http://localhost:8000/docs")
    print("  AI/ML Recommender      : http://localhost:8001")
    print("  Supabase Database      : Connected & Active")
    print(sep)

    # Start ML service in background thread
    ml_thread = threading.Thread(target=run_ml_service, daemon=True)
    ml_thread.start()

    time.sleep(1)

    # Open browser
    def open_browser():
        time.sleep(1.5)
        print("[*] Opening FoodBook in your browser: http://localhost:8000 ...")
        webbrowser.open("http://localhost:8000")

    threading.Thread(target=open_browser, daemon=True).start()

    # Start FastAPI Backend (main process)
    run_backend()
