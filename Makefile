cli: setup
	cd src
	../env/bin/python -m harmony.cli

test: setup
	env/bin/nosetests -w src test

setup:
	virtualenv env
	env/bin/pip install -r requirements.txt

.PHONY: clean
clean:
	pyclean src
