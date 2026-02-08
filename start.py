"""
SikkaTrade Auto-Launcher
Author: Hassan Ali (@softdevhassan)

This script automatically starts both the trading engine and Streamlit dashboard.
Run: python start.py
"""

import subprocess
import sys
import time
import os
from pathlib import Path


def main():
    print("=" * 60)
    print("[$] SikkaTrade Auto-Launcher")
    print("   Author: Hassan Ali (@softdevhassan)")
    print("=" * 60)
    print()

    # Get the project directory
    project_dir = Path(__file__).parent

    # --- Clean up previous run files ---
    print("[*] Cleaning up previous session logs and state...")

    # 1. Clear logs
    log_file = project_dir / "logs" / "sikkatrade.log"
    try:
        if log_file.exists():
            with open(log_file, "w") as f:
                f.write("")  # Clear content
            print("    - Cleared logs/sikkatrade.log")
    except Exception as e:
        print(f"    ! Failed to clear log file: {e}")

    # 2. Clear state.json
    state_file = project_dir / "state.json"
    try:
        if state_file.exists():
            state_file.unlink()  # Delete file
            print("    - Removed old state.json")
    except Exception as e:
        print(f"    ! Failed to remove state.json: {e}")

    # --- End clean up ---

    # Start the trading engine
    print("[*] Starting trading engine (app.py)...")
    engine_process = subprocess.Popen(
        [sys.executable, "app.py"],
        cwd=project_dir,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
        encoding="utf-8",  # Force UTF-8 for Windows
        bufsize=1,
    )

    # Wait for state.json to be created
    state_file = project_dir / "state.json"
    print("[*] Waiting for engine to initialize...")

    for i in range(10):  # Wait up to 10 seconds
        if state_file.exists():
            print("[+] Engine initialized successfully!")
            break
        time.sleep(1)
    else:
        print("[!] Warning: state.json not created yet, but continuing...")

    time.sleep(1)

    # Launch Streamlit dashboard
    print("[*] Launching Streamlit dashboard...")
    print()

    streamlit_process = subprocess.Popen(
        [sys.executable, "-m", "streamlit", "run", "gui.py", "--server.headless=false"],
        cwd=project_dir,
    )

    print("=" * 60)
    print("[+] Both engine and dashboard are running!")
    print("   Press Ctrl+C to stop all processes")
    print("=" * 60)
    print()
    print("[>] Engine Logs:")
    print("-" * 60)

    try:
        # Stream engine output to console
        for line in engine_process.stdout:
            print(line, end="")

        # Engine has exited (auto-shutdown or error)
        engine_exit_code = engine_process.wait()

        print("\n\n[!] Engine has stopped (exit code: {})".format(engine_exit_code))
        print("[*] Terminating Streamlit dashboard...")

        streamlit_process.terminate()
        streamlit_process.wait(timeout=5)

        print("[+] All processes stopped. Goodbye!")
        sys.exit(0)

    except KeyboardInterrupt:
        print("\n\n[!] Manual shutdown requested...")
        engine_process.terminate()
        streamlit_process.terminate()

        # Wait for processes to finish
        try:
            engine_process.wait(timeout=5)
            streamlit_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            engine_process.kill()
            streamlit_process.kill()

        print("[+] All processes stopped. Goodbye!")
        sys.exit(0)


if __name__ == "__main__":
    main()
