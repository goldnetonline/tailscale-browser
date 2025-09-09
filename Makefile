# Makefile for Tailscale Browser

.PHONY: help install lint format test build freeze clean

help:
	@echo "Tailscale Browser Makefile"
	@echo "Available targets:"
	@echo "  install   Install dependencies (using poetry or pip)"
	@echo "  lint      Run flake8 and pylint checks"
	@echo "  format    Auto-format code with black"
	@echo "  test      Run tests (none yet)"
	@echo "  build     Build standalone executables for all OSes (requires PyInstaller)"
	@echo "  clean     Remove build artifacts"

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
	pyinstaller --onefile --windowed --icon=icon.png tailscale_browser.py

clean:
	rm -rf __pycache__ build dist *.spec
