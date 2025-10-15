#!/usr/bin/env python3
"""Format all Python files in the project using black and isort."""

import os
import subprocess
import sys


def run_command(command, description=None):
    """Run a shell command and return success status."""
    if description:
        print(f"\n🔧 {description}...")
    else:
        print(f"\n🔧 Running: {command}")

    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ Success: {command}")
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed: {command}")
        if e.stdout:
            print("Output:", e.stdout)
        if e.stderr:
            print("Error:", e.stderr)
        return False


def main():
    """Format Python files."""
    print("🐍 Formatting Python files...")

    # Get all Python files in the project
    python_files = []
    for root, dirs, files in os.walk("."):
        # Skip virtual environments and build directories
        if any(
            skip in root
            for skip in ["venv", ".venv", "env", "__pycache__", "build", "dist", "node_modules"]
        ):
            continue

        for file in files:
            if file.endswith(".py"):
                python_files.append(os.path.join(root, file))

    if not python_files:
        print("No Python files found to format.")
        return

    print(f"Found {len(python_files)} Python files to format.")

    # Run isort to organize imports
    isort_success = run_command("isort .", "Organizing imports with isort")

    # Run black to format code
    black_success = run_command("black .", "Formatting code with Black")

    # Run flake8 for linting (won't fix, just report)
    flake8_success = run_command("flake8 .", "Checking code quality with flake8")

    if all([isort_success, black_success]):
        print("\n🎉 Python formatting completed successfully!")
        if not flake8_success:
            print("💡 Note: Some linting issues found. Check the output above.")
    else:
        print("\n💥 Python formatting completed with errors.")
        sys.exit(1)


if __name__ == "__main__":
    main()
