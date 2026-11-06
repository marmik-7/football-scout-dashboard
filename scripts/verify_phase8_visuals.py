"""
Verification script for SCOUT Phase 8: Scouting Intelligence & Simplification.
Spins up Dash on port 8062, captures high-resolution screenshots of updated modules,
and saves them to the conversation artifact directory.
"""

import os
import sys
import time
import subprocess
import urllib.request

CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
ARTIFACT_DIR = r"C:\Users\marmi\.gemini\antigravity\brain\83139e12-873e-4357-b459-0f4266f9bb15"
PORT = 8062


def wait_for_server(url, timeout=15):
    start = time.time()
    while time.time() - start < timeout:
        try:
            with urllib.request.urlopen(url) as response:
                if response.status == 200:
                    return True
        except Exception:
            time.sleep(0.5)
    return False


def capture_screenshot(url, output_path, width=1400, height=900):
    cmd = [
        CHROME_PATH,
        "--headless=new",
        "--disable-gpu",
        "--hide-scrollbars",
        f"--window-size={width},{height}",
        f"--screenshot={output_path}",
        url,
    ]
    subprocess.run(cmd, check=True, timeout=15)


def main():
    print(f"Starting SCOUT on port {PORT}...")
    server_process = subprocess.Popen(
        [sys.executable, "-c", f"from app.app import app; app.run(port={PORT}, debug=False)"],
        cwd=os.path.abspath(os.path.join(os.path.dirname(__file__), "..")),
    )

    try:
        base_url = f"http://127.0.0.1:{PORT}"
        if not wait_for_server(base_url):
            print("Error: Server failed to start within timeout.")
            return False

        print("Server live! Capturing Phase 8 verification screenshots...")
        pages_to_capture = [
            ("profile_haaland_scout", f"{base_url}/player-profile?player=Erling+Haaland"),
            ("profile_saliba_scout", f"{base_url}/player-profile?player=William+Saliba"),
            ("similar_trent_scout", f"{base_url}/similar-players?player=Trent+Alexander-Arnold"),
            ("comparison_saliba_vvd", f"{base_url}/player-comparison?player1=William+Saliba&player2=Virgil+van+Dijk"),
            ("styles_scout", f"{base_url}/playing-styles"),
            ("explorer_scout", f"{base_url}/player-explorer"),
        ]

        for name, url in pages_to_capture:
            out_file = os.path.join(ARTIFACT_DIR, f"{name}.png")
            print(f"Capturing {name} -> {out_file}...")
            capture_screenshot(url, out_file)
            print(f"Saved {name}.png ({os.path.getsize(out_file):,} bytes)")

        print("\nAll Phase 8 visual captures complete!")
        return True

    finally:
        print("Shutting down temporary test server...")
        server_process.terminate()
        try:
            server_process.wait(timeout=3)
        except subprocess.TimeoutExpired:
            server_process.kill()


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
