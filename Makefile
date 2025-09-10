
# Makefile for Tailscale Browser

.PHONY: help install lint format test build build-windows package package-windows clean run optimize optimize-test

help:
	@echo "Tailscale Browser Makefile"
	@echo "Available targets:"
	@echo "  install         Install dependencies (using poetry)"
	@echo "  lint            Run flake8 and pylint checks"
	@echo "  format          Auto-format code with black"
	@echo "  test            Run tests (none yet)"
	@echo "  build           Build standalone executable (macOS, optimized)"
	@echo "  build-windows   Build standalone executable (Windows)"
	@echo "  package         Build ALL distribution packages (macOS)"
	@echo "  package-windows Build ALL distribution packages (Windows)"
	@echo "  run             Run the app using poetry"
	@echo "  clean           Remove build artifacts"

run:
	poetry run python tailscale_browser.py

install:
	poetry install

lint:
	poetry run flake8 tailscale_browser.py
	poetry run pylint tailscale_browser.py

format:
	poetry run black tailscale_browser.py

test:
	@echo "No tests yet."

build:
	@echo "🔨 Building optimized standalone executable (macOS)..."
	@if [ ! -f icon.icns ]; then \
		poetry run python -c "from PIL import Image; img = Image.open('icon.png'); img.save('icon.icns', format='ICNS')"; \
	fi
	poetry run pyinstaller --onefile --windowed --name "TailscaleBrowser" --icon=icon.icns \
		--exclude-module tkinter \
		--exclude-module matplotlib \
		--exclude-module numpy \
		--exclude-module pandas \
		--exclude-module scipy \
		--exclude-module PIL.ImageTk \
		--exclude-module PIL.ImageQt \
		--strip \
		--optimize=2 \
		tailscale_browser.py

build-windows:
	@echo "🔨 Building standalone executable (Windows)..."
	@echo "Note: Run this on a Windows machine with Python and Poetry installed"
	poetry run pyinstaller --onefile --windowed --name "TailscaleBrowser.exe" \
		--exclude-module tkinter \
		--exclude-module matplotlib \
		--exclude-module numpy \
		--exclude-module pandas \
		--exclude-module scipy \
		--exclude-module PIL.ImageTk \
		--exclude-module PIL.ImageQt \
		--strip \
		--optimize=2 \
		tailscale_browser.py

package:
	@echo "📦 Building ALL distribution packages (macOS, optimized)..."
	@echo "🧹 Cleaning previous builds..."
	rm -rf build dist release *.spec
	@echo "🎨 Creating ICNS icon..."
	@if [ ! -f icon.icns ]; then \
		poetry run python -c "from PIL import Image; img = Image.open('icon.png'); img.save('icon.icns', format='ICNS')"; \
		echo "✅ Created icon.icns from icon.png"; \
	else \
		echo "✅ icon.icns already exists"; \
	fi
	@echo "🐍 Building Python wheel..."
	poetry build
	@echo "🔨 Building optimized executable with app bundle..."
	poetry run pyinstaller --onedir --windowed --name "TailscaleBrowser" --icon=icon.icns \
		--add-data "icon.png:." \
		--osx-bundle-identifier "com.goldnetonline.tailscale-browser" \
		--exclude-module tkinter \
		--exclude-module matplotlib \
		--exclude-module numpy \
		--exclude-module pandas \
		--exclude-module scipy \
		--exclude-module PIL.ImageTk \
		--exclude-module PIL.ImageQt \
		--strip \
		--optimize=2 \
		tailscale_browser.py
	@echo "📱 Creating release files..."
	mkdir -p release
	cp "dist/tailscale_browser-"*"-py3-none-any.whl" "release/" 2>/dev/null || true
	cp "dist/tailscale_browser-"*".tar.gz" "release/" 2>/dev/null || true
	if [ -d "dist/TailscaleBrowser.app" ]; then \
		cp -R "dist/TailscaleBrowser.app" "release/Tailscale Browser.app"; \
		cd dist && zip -r "../release/Tailscale-Browser-macOS.app.zip" "TailscaleBrowser.app"; cd ..; \
	elif [ -d "dist/TailscaleBrowser" ]; then \
		mkdir -p "release/Tailscale Browser.app/Contents/MacOS"; \
		mkdir -p "release/Tailscale Browser.app/Contents/Resources"; \
		cp "dist/TailscaleBrowser/TailscaleBrowser" "release/Tailscale Browser.app/Contents/MacOS/"; \
		cp -R "dist/TailscaleBrowser/_internal" "release/Tailscale Browser.app/Contents/"; \
		cp icon.png "release/Tailscale Browser.app/Contents/Resources/"; \
		echo '<?xml version="1.0" encoding="UTF-8"?>' > "release/Tailscale Browser.app/Contents/Info.plist"; \
		echo '<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">' >> "release/Tailscale Browser.app/Contents/Info.plist"; \
		echo '<plist version="1.0"><dict>' >> "release/Tailscale Browser.app/Contents/Info.plist"; \
		echo '<key>CFBundleName</key><string>Tailscale Browser</string>' >> "release/Tailscale Browser.app/Contents/Info.plist"; \
		echo '<key>CFBundleIdentifier</key><string>com.goldnetonline.tailscale-browser</string>' >> "release/Tailscale Browser.app/Contents/Info.plist"; \
		echo '<key>CFBundleVersion</key><string>0.1.0</string>' >> "release/Tailscale Browser.app/Contents/Info.plist"; \
		echo '<key>CFBundleExecutable</key><string>TailscaleBrowser</string>' >> "release/Tailscale Browser.app/Contents/Info.plist"; \
		echo '<key>CFBundleIconFile</key><string>icon.png</string>' >> "release/Tailscale Browser.app/Contents/Info.plist"; \
		echo '</dict></plist>' >> "release/Tailscale Browser.app/Contents/Info.plist"; \
		cd dist && zip -r "../release/Tailscale-Browser-macOS.app.zip" "TailscaleBrowser"; cd ..; \
	fi
	if [ -f "dist/TailscaleBrowser/TailscaleBrowser" ]; then \
		cp "dist/TailscaleBrowser/TailscaleBrowser" "release/TailscaleBrowser-standalone"; \
		chmod +x "release/TailscaleBrowser-standalone"; \
	fi
	@echo ""
	@echo "✅ ALL packages built successfully!"
	@echo "📂 Release files:"
	@ls -la release/
	@echo ""
	@echo "🚀 Ready for distribution!"

package-windows:
	@echo "📦 Building ALL distribution packages (Windows)..."
	@echo "Note: Run this on a Windows machine with Python and Poetry installed"
	@echo "🧹 Cleaning previous builds..."
	rm -rf build dist release *.spec
	@echo "🐍 Building Python wheel..."
	poetry build
	@echo "🔨 Building optimized Windows executable..."
	poetry run pyinstaller --onedir --windowed --name "TailscaleBrowser" \
		--exclude-module tkinter \
		--exclude-module matplotlib \
		--exclude-module numpy \
		--exclude-module pandas \
		--exclude-module scipy \
		--exclude-module PIL.ImageTk \
		--exclude-module PIL.ImageQt \
		--strip \
		--optimize=2 \
		tailscale_browser.py
	@echo "📱 Creating release files..."
	mkdir -p release
	cp "dist/tailscale_browser-"*"-py3-none-any.whl" "release/" 2>/dev/null || true
	cp "dist/tailscale_browser-"*".tar.gz" "release/" 2>/dev/null || true
	if [ -d "dist/TailscaleBrowser" ]; then \
		cp -R "dist/TailscaleBrowser" "release/TailscaleBrowser-Windows"; \
		cd dist && zip -r "../release/Tailscale-Browser-Windows.zip" "TailscaleBrowser"; cd ..; \
	fi
	@echo ""
	@echo "✅ ALL packages built successfully!"
	@echo "📂 Release files:"
	@ls -la release/
	@echo ""
	@echo "🚀 Ready for distribution!"

clean:
	rm -rf __pycache__ build dist release *.spec
