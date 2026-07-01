# Tailscale Browser - Windows Build Script
# Run this in PowerShell on Windows

Write-Host "Building Tailscale Browser for Windows..." -ForegroundColor Green

# Check if Poetry is installed
try {
    python -m poetry --version | Out-Null
    Write-Host "Poetry found" -ForegroundColor Green
} catch {
    Write-Host "Poetry not found. Installing..." -ForegroundColor Yellow
    python -m pip install --user poetry
}

# Install dependencies
Write-Host "Installing dependencies..." -ForegroundColor Yellow
python -m poetry install

# Build the executable
Write-Host "Building Windows executable..." -ForegroundColor Yellow
python -m poetry run pyinstaller --onefile --windowed --name "Tailscale Browser" `
    --paths src `
    --add-data "resources;resources" `
    --hidden-import PyQt5.QtWebEngineWidgets `
    --exclude-module tkinter `
    --exclude-module matplotlib `
    --exclude-module numpy `
    --exclude-module pandas `
    --exclude-module scipy `
    --strip `
    --optimize=2 `
    src/tailscale_browser/main.py

# Check if build was successful
if (Test-Path ".\dist\Tailscale Browser.exe") {
    $size = (Get-Item ".\dist\Tailscale Browser.exe").Length / 1MB
    Write-Host "Build complete!" -ForegroundColor Green
    Write-Host "Executable location: dist\Tailscale Browser.exe" -ForegroundColor Cyan
    Write-Host "Size: $([math]::Round($size, 2)) MB" -ForegroundColor Cyan
    Write-Host "You can now run: .\dist\Tailscale Browser.exe" -ForegroundColor Yellow
} else {
    Write-Host "Build failed. Check the output above for errors." -ForegroundColor Red
    exit 1
}
