import subprocess, sys
sys.path.insert(0, ".")
result = subprocess.run(
    [sys.executable, "-m", "pytest", "tests/", "-v", "--tb=short"],
    capture_output=False
)
sys.exit(result.returncode)
