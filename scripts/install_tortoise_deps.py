"""
Install only tortoise-tts dependencies without 'deepspeed'.
"""

from pathlib import Path
import subprocess
import sys

def main():


    req_file = Path("external/tortoise-tts/requirements.txt")

    if not req_file.exists():
        print(f"❌ Error: requirements.txt not found at {req_file}")
        sys.exit(1)

    try:
        # Read end filter the dependencies
        with open(req_file, encoding='utf-8') as f:
            lines = [
                line.strip()
                for line in f
                if line.strip() and not line.startswith("#") and "deepspeed" not in line
            ]
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
    try:       
        # Install filtered dependencies
        print("📦 Installing filtered dependencies from Tortoise TTS...")
        subprocess.run(["pip", "install", *lines], check=True)
        print("Udate dependency: pip install transformers==4.21.1")
        subprocess.run(["pip", "install", "transformers==4.21.1"], check=True)
        print("✅ Dependencies installed successfully (without deepspeed).")
    except subprocess.CalledProcessError as e:
        print("❌ Pip installation failed.")
        sys.exit(e.returncode)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()