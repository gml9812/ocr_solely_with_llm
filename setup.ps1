# setup.ps1
# Try different ways to find Python 3.10
$pythonPaths = @(
    "py -3.10",  # This should be first as it's the most reliable way
    "python3.10",
    "python310",
    "C:\Users\$env:USERNAME\AppData\Local\Programs\Python\Python310\python.exe",
    "C:\Program Files\Python310\python.exe",
    "C:\Python310\python.exe"
)

$python310Path = $null
foreach ($path in $pythonPaths) {
    try {
        if ($path -eq "py -3.10") {
            $version = & py -3.10 -c "import sys; print(sys.version.split()[0])" 2>$null
        } else {
            $version = & $path -c "import sys; print(sys.version.split()[0])" 2>$null
        }
        if ($version -and $version.StartsWith("3.10")) {
            $python310Path = $path
            break
        }
    } catch {
        continue
    }
}

if (-not $python310Path) {
    Write-Host "Error: Python 3.10.x is required but not found."
    Write-Host "Please ensure Python 3.10 is installed and Python Launcher (py) is available."
    exit 1
}

Write-Host "Found Python 3.10 at: $python310Path"

# Create virtual environment if it doesn't exist
if (-not (Test-Path ".\venv")) {
    Write-Host "Creating virtual environment..."
    if ($python310Path -eq "py -3.10") {
        & py -3.10 -m venv venv
    } else {
        & $python310Path -m venv venv
    }
    Write-Host "Virtual environment created successfully!"
    Write-Host "To activate, run: .\venv\Scripts\activate"
} else {
    Write-Host "Virtual environment already exists."
}

# Activate virtual environment and install dependencies
Write-Host "Activating virtual environment and installing dependencies..."
.\venv\Scripts\activate.ps1

# Install pip requirements with SSL verification disabled
Write-Host "Installing dependencies (with SSL verification disabled)..."
pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org -r requirements.txt

Write-Host "Setup complete! Virtual environment is ready."
Write-Host "To activate the virtual environment, run: .\venv\Scripts\activate"

Write-Host "`nSetup complete. Press Enter to exit..."
Read-Host 
 