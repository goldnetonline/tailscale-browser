# Tailscale Browser

Tailscale Browser is an open source, cross-platform, tabbed browser for quickly accessing URLs or IPs (such as Tailscale nodes) with a beautiful purple-themed UI. It stores recent addresses and other settings in a config file in your home directory.

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.

# Tailscale Browser - Documentation

## Features

-   Tabbed browser interface (add/remove tabs)
-   Each tab loads a URL/IP in a modern browser view (Qt WebEngine)
-   Add tab dialog lets you pick from recent addresses or enter a new one (with name and URL/IP)
-   Recent addresses are stored in a config file in your home directory
-   Purple color theme and a sample launcher icon (`icon.png`)
-   The browser view takes up maximum space

## Requirements

-   Python 3.10+
-   PyQt5, PyQtWebEngine
-   (Optional) Poetry for dependency management
-   (Optional) PyInstaller for bundling

## Setup

### 1. Python Environment

-   Install [pyenv](https://github.com/pyenv/pyenv) and run:
    ```sh
    pyenv install 3.10.13
    pyenv local 3.10.13
    ```

### 2. Install Dependencies

```sh
poetry install
```

### 3. Pre-commit Hooks

-   Install pre-commit:
    ```sh
    pip install pre-commit
    pre-commit install
    ```

### 4. Run the App

```sh
python tailscale_browser.py
```

Or with Poetry:

```sh
poetry run python tailscale_browser.py
```

## Linting & Formatting

-   Run `make lint` to check code style (flake8, pylint)
-   Run `make format` to auto-format with black

## Bundling for Any OS

-   Install PyInstaller:
    ```sh
    poetry add --dev pyinstaller
    ```
-   Build a standalone executable:
    ```sh
    make build
    ```
    The output will be in the `dist/` folder.
-   For Windows/macOS/Linux, run the above on the target OS or use a cross-compilation tool/docker.

## Cleaning Up

-   Run `make clean` to remove build artifacts.

## Notes

-   Recent addresses are stored in `~/.tailscale_browser_recent.json`.
-   You can change the launcher icon by replacing `icon.png`.
-   For advanced packaging (e.g., .dmg, .msi, .deb), see PyInstaller and platform-specific docs.

---

Enjoy using Tailscale Browser!
