# TailScale Browser

A minimal, tabbed browser application built with Python and PyQt5, designed for accessing TailScale admin interfaces with SSL certificate bypass capabilities.

## Features

-   🌐 **Tabbed Browsing**: Multiple tabs with easy navigation
-   🎨 **Dark Mode Interface**: Chrome-like dark theme for comfortable viewing
-   🔒 **SSL Bypass**: Automatically accepts self-signed certificates for development environments
-   ➕ **Quick Tab Management**: New tab button and close buttons on each tab
-   🚀 **Lightweight**: Optimized build (101MB) with 63% size reduction
-   🖥️ **Cross-Platform**: Builds for macOS and Windows

## Quick Start

### Cross-Platform Builds

```bash
# macOS (native)
make build

# Windows (requires Windows environment)
make build-windows
```

### Manual Installation

```bash
# Install dependencies
poetry install

# Run directly
poetry run tailscale-browser

# Build standalone binary
make build
```

## 📦 Installation Methods

### Option 1: Python Package

```bash
pip install tailscale-browser
tailscale-browser
```

### Option 2: From Source

```bash
poetry install
poetry run tailscale-browser
```

### Option 3: Standalone Executable

Download from releases or build yourself (see Building section).

## 🛠️ Development

### Requirements

-   Python 3.13+
-   Poetry (recommended) or pip
-   PyQt5 & PyQtWebEngine

### Linux / WSL2 (Ubuntu) System Dependencies

If you're running on Linux or WSL2 (Ubuntu), install the Qt and audio runtime libs:

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

-   **Windows 11 (WSLg)**: GUI apps should work out of the box.
-   **Windows 10 or no WSLg**: Run an X server on Windows (VcXsrv/X410) and set `DISPLAY` in WSL:

```bash
export DISPLAY=$(grep nameserver /etc/resolv.conf | awk '{print $2}'):0
```

If you see OpenGL/GLX errors on WSL2, try software rendering:

```bash
LIBGL_ALWAYS_SOFTWARE=1 QT_OPENGL=software poetry run tailscale-browser
```

### Setup Development Environment

```bash
# Install Poetry if you haven't already
curl -sSL https://install.python-poetry.org | python3 -

# Clone and setup
git clone https://github.com/goldnetonline/tailscale-browser.git
cd tailscale-browser
poetry install

# Install pre-commit hooks
poetry run pre-commit install

# Run the application
make run
```

### Development Commands

```bash
make help          # Show all available commands
make run           # Run the application
make format        # Format code with black
make lint          # Run linting checks
make test          # Run tests (when available)
```

## 📦 Building & Packaging

### One-Command Build (All Packages)

```bash
# Build everything at once - creates all distribution packages
make package
```

### Development Commands

```bash
# Quick executable build only
make build

# Clean all build artifacts
make clean
```

### Cross-Platform Building

-   **macOS**: Run `make package` to create `.app` bundle
-   **Linux**: Run `make build` to create executable
-   **Windows**: Run `make build` on Windows system

## 🎯 Usage

1. **Launch the app** using any of the installation methods above
2. **Add a new tab** by clicking the "+ New Tab" button
3. **Enter URL or IP** in the dialog (e.g., `192.168.1.100`, `tailscale-device.local`)
4. **Give it a name** for easy identification
5. **Browse securely** - SSL certificate errors are automatically bypassed

### Perfect for:

-   🖥️ **PiKVM Access**: Web-based KVM over IP
-   🏠 **Home Lab Services**: Router interfaces, NAS systems, IoT devices
-   🔗 **Tailscale Nodes**: Quick access to your mesh network devices
-   🌐 **Local Development**: Test servers and development environments

## ⚙️ Configuration

Configuration is automatically stored in `~/.tailscale_browser`:

```json
{
    "recent": [
        {
            "name": "Pi-KVM",
            "url": "https://192.168.1.100"
        }
    ]
}
```

## 🧹 Maintenance

```bash
# Clean build artifacts
make clean

# Update dependencies
poetry update

# Run pre-commit on all files
poetry run pre-commit run --all-files
```

## 📄 License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests and linting (`make format lint`)
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## 🐛 Issues & Support

-   🐛 [Report Bugs](https://github.com/goldnetonline/tailscale-browser/issues)
-   💡 [Request Features](https://github.com/goldnetonline/tailscale-browser/issues)
-   📖 [Documentation](https://github.com/goldnetonline/tailscale-browser/wiki)

---

**Enjoy browsing your Tailscale network! 🎉**
