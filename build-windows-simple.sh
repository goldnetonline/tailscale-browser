#!/bin/bash
# Simple Windows build using PyInstaller bootloader for Windows
# This is easier and faster than full Wine setup

set -e

echo "🔨 Building Windows executable from WSL2..."

# Ensure PyInstaller is installed
poetry run pip install pyinstaller

# Create a spec file for Windows
cat > TailscaleBrowser-windows.spec << 'EOF'
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['src/tailscale_browser/main.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'matplotlib', 'numpy', 'pandas', 'scipy'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='TailscaleBrowser',
    debug=False,
    bootloader_ignore_signals=False,
    strip=True,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
EOF

# Note: This creates the spec file, but PyInstaller still needs Windows Python to actually build
echo "⚠️  Note: To build for Windows, you have two options:"
echo ""
echo "Option 1: Use the Wine script (more complex, full Wine setup)"
echo "  ./build-windows-wine.sh"
echo ""
echo "Option 2: Transfer files to Windows and build there (recommended)"
echo "  - Copy the entire project folder to Windows"
echo "  - On Windows, run: build-windows.ps1"
echo ""
echo "Option 3: Use GitHub Actions / CI to build Windows version"
echo "  - Push to GitHub and set up Windows CI pipeline"
echo ""
echo "📝 Spec file created: TailscaleBrowser-windows.spec"
