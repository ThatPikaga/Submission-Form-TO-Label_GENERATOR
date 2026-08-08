import os
import subprocess
import sys

def is_virtual_env():
    """Check if the script is running inside a virtual environment."""
    return sys.prefix != sys.base_prefix

def run_command(command_list):
    """Run a system command and return True if successful."""
    try:
        subprocess.check_call(command_list)
        return True
    except subprocess.CalledProcessError:
        return False

def setup_and_install():
    requirements_file = "requirements.txt"
    
    # 1. Verify requirements file exists
    if not os.path.exists(requirements_file):
        print(f"\n[ERROR] Could not find '{requirements_file}' in this folder.")
        print("Please ensure 'requirements.txt' is in the same folder as this script.")
        return

    # 2. Block user from using sudo to prevent system package corruption
    if os.name != 'nt' and os.geteuid() == 0:
        print("\n[ERROR] Do not run this script with sudo.")
        print("Please run it as a normal user: python install_requirements.py")
        return

    # 3. Handle Arch Linux / Linux environment safety
    if os.name != 'nt' and not is_virtual_env():
        print("\n[INFO] Linux environment detected. Setting up an isolated virtual environment...")
        
        venv_dir = os.path.join(os.getcwd(), "venv")
        python_bin = os.path.join(venv_dir, "bin", "python")
        
        # Create virtual environment if it doesn't exist
        if not os.path.exists(venv_dir):
            print("Creating 'venv' folder...")
            if not run_command([sys.executable, "-m", "venv", "venv"]):
                print("[ERROR] Failed to create virtual environment. Ensure 'python-virtualenv' is installed via pacman.")
                return
        
        print("Installing packages inside the virtual environment...")
        # Upgrade pip first, then install requirements using the environment's python binary
        run_command([python_bin, "-m", "pip", "install", "--upgrade", "pip"])
        success = run_command([python_bin, "-m", "pip", "install", "-r", requirements_file])
        
        if success:
            print("\n[SUCCESS] Environment configured perfectly!")
            print(f"To run your label generator tool, use this command:")
            print(f"  ./venv/bin/python your_label_script.py\n")
        else:
            print("\n[ERROR] Installation failed inside the virtual environment.")
        return

    # 4. Standard Installation (Windows or already active Virtual Environment)
    print("Installing packages from requirements.txt...")
    success = run_command([sys.executable, "-m", "pip", "install", "-r", requirements_file])
    
    if success:
        print("\n[SUCCESS] All requirements installed successfully!")
    else:
        print("\n[ERROR] Installation failed.")

if __name__ == "__main__":
    setup_and_install()
