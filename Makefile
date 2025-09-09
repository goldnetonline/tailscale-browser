
# Makefile for Tailscale Browser

.PHONY: help install lint format test build freeze clean run

help:
	@echo "Tailscale Browser Makefile"
	@echo "Available targets:"
	@echo "  install   Install dependencies (using poetry)"
	@echo "  lint      Run flake8 and pylint checks"
	@echo "  format    Auto-format code with black"
	@echo "  test      Run tests (none yet)"
	@echo "  build     Build standalone executables for all OSes (requires PyInstaller)"
	@echo "  run       Run the app using poetry"
	@echo "  clean     Remove build artifacts"
run:
	poetry run python tailscale_browser.py

install:
	poetry install

lint:
	flake8 tailscale_browser.py
	pylint tailscale_browser.py

format:
	black tailscale_browser.py

test:
	@echo "No tests yet."

build:
	pyinstaller --onefile --windowed --icon=icon.svg tailscale_browser.py

clean:
	rm -rf __pycache__ build dist *.spec
