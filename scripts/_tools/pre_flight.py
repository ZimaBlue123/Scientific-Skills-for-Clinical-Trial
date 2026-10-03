import os
import sys


def pre_flight_check(target_path, required_packages=None):
    """
    ECC-style AgentShield pre-flight check.
    Validates if the intended write path is safe and if required dependencies exist.
    """
    print(f"[AgentShield] Initiating pre-flight check for target: {target_path}")

    # 1. Path Safety Check (Write Pre-Check)
    # Ensure the script isn't trying to write to a random location outside the project/scripts
    abs_target = os.path.abspath(target_path)
    # Get the project root assuming this script is in scripts/_tools/
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

    if not abs_target.startswith(project_root):
        print(
            f"[AgentShield Error] Target path {abs_target} is OUTSIDE the project root {project_root}!"
        )
        sys.exit(1)

    print("[AgentShield] Path safety check passed.")

    # 2. Dependency Check (Optional)
    if required_packages:
        import importlib.util

        missing = []
        for pkg in required_packages:
            if importlib.util.find_spec(pkg) is None:
                missing.append(pkg)
        if missing:
            print(f"[AgentShield Error] Missing dependencies: {', '.join(missing)}")
            print("Please run: pip install -r requirements.txt")
            sys.exit(1)

        print("[AgentShield] Dependency check passed.")

    print("[AgentShield] Pre-flight complete. Proceeding with execution.\n")
    return True


if __name__ == "__main__":
    # Test run
    pre_flight_check(os.path.join(os.path.dirname(__file__), "test.py"), ["docx"])
