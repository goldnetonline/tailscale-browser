#!/bin/bash
# Cross-compile Tailscale Browser for Windows from WSL2 using Wine
# This script builds a Windows .exe from Linux/WSL2

set -e

echo "🍷 Building Tailscale Browser for Windows using Wine..."

# Check if Wine is installed
if ! command -v wine &> /dev/null; then
    echo "❌ Wine is not installed. Installing..."
    sudo apt update
    sudo apt install -y wine64
fi

echo "✓ Wine is ready"

# Initialize Wine prefix if needed
export WINEPREFIX="$HOME/.wine-pyinstaller"
export WINEARCH=win64

if [ ! -d "$WINEPREFIX" ]; then
    echo "🔧 Setting up Wine environment (first time only)..."
    wineboot -u
    sleep 3
fi

# Download Python for Windows if not already present
PYTHON_VERSION="3.11.9"
PYTHON_INSTALLER="python-${PYTHON_VERSION}-amd64.exe"
PYTHON_URL="https://www.python.org/ftp/python/${PYTHON_VERSION}/${PYTHON_INSTALLER}"

if [ ! -f "$WINEPREFIX/drive_c/Python311/python.exe" ]; then
    echo "📥 Downloading Python for Windows..."
    wget -q --show-progress "$PYTHON_URL" -O "/tmp/$PYTHON_INSTALLER"

    echo "📦 Installing Python in Wine..."
    wine "/tmp/$PYTHON_INSTALLER" /quiet InstallAllUsers=1 PrependPath=1 Include_test=0
    sleep 5

    rm "/tmp/$PYTHON_INSTALLER"
fi

echo "✓ Python for Windows is ready"

# Install PyInstaller in Wine
echo "📦 Installing PyInstaller for Windows..."
wine "$WINEPREFIX/drive_c/Python311/python.exe" -m pip install --upgrade pip pyinstaller pyqt5 pyqt5-tools

# Copy project files to Wine drive
WINE_PROJECT_DIR="$WINEPREFIX/drive_c/tailscale-browser"
mkdir -p "$WINE_PROJECT_DIR"
cp -r src resources pyproject.toml poetry.lock "$WINE_PROJECT_DIR/" 2>/dev/null || cp -r src resources "$WINE_PROJECT_DIR/"

# Build Windows executable
echo "🔨 Building Windows executable..."
cd "$WINE_PROJECT_DIR"

wine "$WINEPREFIX/drive_c/Python311/Scripts/pyinstaller.exe" \
    --onefile \
    --windowed \
    --name "TailscaleBrowser" \
    --paths src \
    --add-data "resources;resources" \
    --hidden-import PyQt5.QtWebEngineWidgets \
    --exclude-module tkinter \
    --exclude-module matplotlib \
    --exclude-module numpy \
    --exclude-module pandas \
    --exclude-module scipy \
    src/tailscale_browser/main.py

# Copy back to project directory
if [ -f "$WINE_PROJECT_DIR/dist/TailscaleBrowser.exe" ]; then
    mkdir -p "$(pwd)/dist/windows"
    cp "$WINE_PROJECT_DIR/dist/TailscaleBrowser.exe" "$(pwd)/dist/windows/"

    SIZE=$(ls -lh "$(pwd)/dist/windows/TailscaleBrowser.exe" | awk '{print $5}')
    echo ""
    echo "✅ Build complete!"
    echo "📍 Location: $(pwd)/dist/windows/TailscaleBrowser.exe"
    echo "📏 Size: $SIZE"
else
    echo "❌ Build failed - executable not found"
    exit 1
fi
