.PHONY: build lint

build: lint
	pyinstaller main.py --onefile

lint:
	flake8 --ignore E501 *.py
