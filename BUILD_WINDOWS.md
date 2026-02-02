# Building Tailscale Browser for Windows

## Prerequisites

1. **Python 3.13+** installed on Windows
2. **Poetry** installed: `pip install poetry`
3. **Git** (to clone the repository)

## Build Instructions

### Step 1: Clone the Repository (if needed)
```powershell
git clone https://github.com/goldnetonline/tailscale-browser.git
cd tailscale-browser
```

### Step 2: Install Dependencies
```powershell
poetry install
```

### Step 3: Build Windows Executable
```powershell
poetry run pyinstaller --onefile --windowed --name "TailscaleBrowser" `
    --exclude-module tkinter `
    --exclude-module matplotlib `
    --exclude-module numpy `
    --exclude-module pandas `
    --exclude-module scipy `
    --strip `
    --optimize=2 `
    tailscale_browser.py
```

### Step 4: Find Your Executable
The built executable will be located at:
```
dist\TailscaleBrowser.exe
```

## Alternative: Use the Makefile (if Make is available)

If you have `make` installed on Windows (via Git Bash, WSL, or Chocolatey):

```bash
make build-windows
```

## Installation

1. Copy `dist\TailscaleBrowser.exe` to any location (e.g., `C:\Program Files\TailscaleBrowser\`)
2. Create a desktop shortcut if desired
3. Run `TailscaleBrowser.exe`

## Notes

- The Windows build will automatically use native Windows styling
- Executable size: ~100-150MB (includes Python runtime and Qt WebEngine)
- No external dependencies required - it's a standalone executable
- The app will look native on Windows with the Windows Vista/11 style

## Troubleshooting

If the build fails:

1. Make sure Python and Poetry are in your PATH
2. Try running from an elevated PowerShell/CMD
3. If PyInstaller is not found, install it manually:
   ```powershell
   poetry run pip install pyinstaller
   ```

## Adding an Icon (Optional)

If you have an icon file:

1. Place `icon.ico` in the project root
2. Add `--icon=icon.ico` to the pyinstaller command:
   ```powershell
   poetry run pyinstaller --onefile --windowed --name "TailscaleBrowser" `
       --icon=icon.ico `
       --exclude-module tkinter `
       --exclude-module matplotlib `
       --exclude-module numpy `
       --exclude-module pandas `
       --exclude-module scipy `
       --strip `
       --optimize=2 `
       tailscale_browser.py
   ```
