.PHONY: build lint

lint:
	flake8 --ignore E501 *.py

build: lint
	echo 'TODO: ansible.errors.AnsibleError: Missing base YAML definition file (bad install?): .../ansible-mock/dist/main/ansible/config/base.yml'
	#pyinstaller main.py --onefile
