# TailScale Browser - Build Guide

## 📊 Size Optimization Results

| Build Type      | Size      | Description                                             |
| --------------- | --------- | ------------------------------------------------------- |
| Regular Build   | 275MB     | Standard PyInstaller build with all Qt components       |
| Optimized Build | **101MB** | **63% size reduction** with selective module exclusions |

## 🚀 Quick Build Commands

### macOS

```bash
# Regular build
make build

# Optimized build (recommended)
make optimize

# Test optimized build
make optimize-test
```

### Windows

For Windows builds, you need to run the commands on a Windows machine with Python and Poetry installed:

```bash
# Regular Windows build
make build-windows

# Optimized Windows build
make optimize-windows

# Package Windows build
make package-windows
```

## 🔧 Build Process

### Prerequisites

-   Python 3.13+
-   Poetry for dependency management
-   PyInstaller for executable creation

### Linux / WSL2 (Ubuntu) Runtime Dependencies

Qt WebEngine requires additional system libraries on Ubuntu/WSL2. Install:

```bash
sudo apt update
sudo apt install -y \
	libasound2t64 \
	libxcb-xinerama0 libxcb-cursor0 libxcb-xkb1 libxkbcommon-x11-0 \
	libxcb1 libx11-xcb1 libxrender1 libxi6 libxtst6 \
	libxcb-keysyms1 libxcb-image0 libxcb-shm0 libxcb-icccm4 \
	libxcb-sync1 libxcb-xfixes0 libxcb-shape0 libxcb-randr0 libxcb-render-util0
```

#### WSL2 GUI Notes

-   **Windows 11 (WSLg)**: GUI apps should work without extra setup.
-   **Windows 10 or no WSLg**: Use an X server (VcXsrv/X410) and set `DISPLAY`:

```bash
export DISPLAY=$(grep nameserver /etc/resolv.conf | awk '{print $2}'):0
```

If you hit OpenGL/GLX errors in WSL2, force software rendering:

```bash
LIBGL_ALWAYS_SOFTWARE=1 QT_OPENGL=software poetry run python tailscale_browser.py
```

### macOS Build Process

1. **Regular Build**: Creates a standard .app bundle (~275MB)
2. **Optimized Build**: Uses `optimized.spec` to exclude unnecessary modules (~101MB)
3. **Packaging**: Creates distributable .app bundle with proper icons

### Windows Build Process

1. **Cross-Platform Note**: Building Windows executables requires a Windows environment
2. **Icon Conversion**: Automatically converts PNG icons to Windows ICO format
3. **Output**: Creates standalone .exe files for Windows distribution

## 📦 Optimization Techniques

The optimized build achieves 63% size reduction through:

### Excluded Modules

-   Development tools (tkinter, matplotlib)
-   Data science libraries (numpy, pandas, scipy)
-   Image processing (PIL components)
-   Qt modules not required for basic web browsing

### Compiler Optimizations

-   `--strip`: Removes debug symbols
-   `--optimize=2`: Maximum Python bytecode optimization
-   Selective Qt framework inclusion

### Binary Stripping

PyInstaller automatically strips debug symbols from:

-   Qt WebEngine components
-   Python extension modules
-   System libraries

## 🏗️ Architecture

### Core Components

-   **Main App**: `tailscale_browser.py` - Tabbed browser with dark mode
-   **Build Config**: `optimized.spec` - PyInstaller optimization settings
-   **Automation**: `Makefile` - Cross-platform build automation

### Dependencies

-   PyQt5/PyQtWebEngine: GUI framework
-   Poetry: Python dependency management
-   PyInstaller: Executable creation
-   Pillow: Icon format conversion

## 📱 Features

### Browser Features

-   ✅ Tabbed browsing with close buttons
-   ✅ Dark mode interface (Chrome-like)
-   ✅ SSL certificate bypass for development
-   ✅ New tab button with instant creation
-   ✅ Proper window management

### Build Features

-   ✅ Cross-platform builds (macOS/Windows)
-   ✅ Size optimization (63% reduction)
-   ✅ Automated icon conversion
-   ✅ Single-command packaging
-   ✅ Professional app bundle creation

## 🎯 Distribution

### macOS

-   **Format**: `.app` bundle
-   **Size**: 101MB (optimized)
-   **Installation**: Drag to Applications folder
-   **Signing**: Unsigned (suitable for development/testing)

### Windows

-   **Format**: `.exe` executable
-   **Size**: ~100MB (estimated)
-   **Installation**: Direct execution
-   **Dependencies**: Self-contained (no external requirements)

## 🔍 Technical Notes

### Qt WebEngine Size

The base Qt WebEngine framework is inherently large (~100MB) because it includes:

-   Full Chromium rendering engine
-   JavaScript V8 engine
-   Network security libraries
-   Media codecs and decoders

### Further Optimization Potential

While 63% reduction is significant, additional optimization could include:

-   Custom Qt build with minimal modules
-   Alternative web rendering (QtWebKit vs WebEngine)
-   Selective Chromium feature exclusion

### Cross-Platform Considerations

-   **Icons**: Automatic conversion (PNG → ICNS/ICO)
-   **Paths**: Platform-specific handling in build scripts
-   **Dependencies**: Poetry ensures consistent environments
-   **Testing**: Platform-specific testing required

## 🚦 Build Status

-   ✅ macOS builds: Working and optimized
-   ✅ Windows builds: Script ready (requires Windows environment)
-   ✅ Size optimization: 275MB → 101MB (63% reduction)
-   ✅ Cross-platform icon support
-   ✅ Automated build pipeline
