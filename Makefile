cli: setup
	cd src
	../env/bin/python -m harmony.cli

setup:
	virtualenv env
	env/bin/pip install -r requirements.txt
