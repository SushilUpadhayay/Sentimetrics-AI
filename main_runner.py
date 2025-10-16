import subprocess
import time
import sys
import os

# List your scripts in the order you want them to run
scripts = [
    "sentiment_analysis.py",
    "news_price_impact.py",
    "historical_price_prediction.py",
    "final_price_prediction.py"  # ✅ Fixed comma typo
]

def run_scripts_in_order():
    python_exec = sys.executable  # ✅ Ensures venv python is used

    print(f"\n🔧 Using Python interpreter: {python_exec}\n")

    for script in scripts:
        script_path = os.path.abspath(script)
        print(f"▶️ Running {script_path}...\n")

        result = subprocess.run([python_exec, script_path], capture_output=True, text=True)

        print(f"⏹️ Completed execution of {script}\n")

        if result.stdout:
            print("📄 Output:")
            print(result.stdout)

        if result.returncode != 0:
            print(f"❌ Error in {script}:")
            print(result.stderr)
            exit
        else:
            print(f"✅ Successfully finished {script}\n")
            time.sleep(2)  # Small delay before next script


if __name__ == "__main__":
    run_scripts_in_order()
