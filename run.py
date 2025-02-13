import os
import sys
import subprocess
import platform

def ensure_venv():
    # Check if we're already in a virtual environment
    if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        return True  # Already in venv
    
    venv_path = os.path.join(os.path.dirname(__file__), 'venv')
    if not os.path.exists(venv_path):
        print("Virtual environment not found. Please run setup.ps1 first.")
        sys.exit(1)
    
    # Determine the activation script based on the OS
    if platform.system() == "Windows":
        activate_script = os.path.join(venv_path, 'Scripts', 'activate.bat')
        activate_cmd = [activate_script]
    else:
        activate_script = os.path.join(venv_path, 'bin', 'activate')
        activate_cmd = ['/bin/bash', '-c', f'source {activate_script} && python {__file__}']
    
    if not os.path.exists(activate_script):
        print("Virtual environment activation script not found.")
        sys.exit(1)
    
    # If not in venv, activate it and restart the script
    if platform.system() == "Windows":
        subprocess.run([activate_script, '&&', 'python', __file__], shell=True)
    else:
        os.execvp(activate_cmd[0], activate_cmd)
    sys.exit(0)

if __name__ == "__main__":
    ensure_venv()
    import uvicorn
    from main import app
    
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info") 