# Tailscale Browser

A modern, tabbed browser application designed for accessing Tailscale networks and local services with SSL bypass support. Features a sleek Chrome-like dark mode interface and convenient recent address management.

## ✨ Features

-   **🗂️ Tabbed Interface**: Add/remove tabs with ease
-   **🌙 Dark Mode**: Chrome-inspired dark theme throughout
-   **🔒 SSL Bypass**: Access PiKVM and other self-signed certificate services
-   **📝 Recent Addresses**: Smart history management with quick access
-   **⚡ Modern WebEngine**: Powered by Qt WebEngine for full web compatibility
-   **🎨 Purple Accent**: Beautiful purple-themed UI elements
-   **💾 Persistent Config**: Settings stored in `~/.tailscale_browser`

## 🚀 Quick Start

### Using Pre-built Releases

1. Download the latest release from [GitHub Releases](https://github.com/goldnetonline/tailscale-browser/releases)
2. **macOS**: Open `Tailscale Browser.app`
3. **Linux/Windows**: Run the executable

### From Source

```bash
# Clone the repository
git clone https://github.com/goldnetonline/tailscale-browser.git
cd tailscale-browser

# Install dependencies
poetry install

# Run the application
make run
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
poetry run python tailscale_browser.py
```

### Option 3: Standalone Executable

Download from releases or build yourself (see Building section).

## 🛠️ Development

### Requirements

-   Python 3.13+
-   Poetry (recommended) or pip
-   PyQt5 & PyQtWebEngine

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
