# setup.ps1
Write-Host "Installing dependencies from requirements.txt..."
pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org -r requirements.txt

Write-Host "`nSetup complete. Press Enter to exit..."
Read-Host 
 