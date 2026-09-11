# Direct PowerShell Phase 2 setup executor
$ProjectRoot = "C:\Users\SUSHANTH\Desktop\AI Customer Intelligence Engine"
cd $ProjectRoot

# Activate venv
& "$ProjectRoot\venv\Scripts\Activate.ps1"

# Run setup and capture output  
Write-Host "Starting Phase 2 setup..." -ForegroundColor Green

# Use subprocess to pass password via stdin
$password = "postgres"
$process = Start-Process -FilePath "python" -ArgumentList "phase2_setup.py" -WorkingDirectory $ProjectRoot -RedirectStandardInput $true -RedirectStandardOutput "phase2_setup_ps.log" -PassThru

# Send password
$process.StandardInput.WriteLine($password)
$process.StandardInput.Close()

# Wait for completion
$process.WaitForExit()

Write-Host "Setup completed. Check phase2_setup_ps.log for details."
Get-Content "$ProjectRoot\phase2_setup_ps.log" -Head 30
