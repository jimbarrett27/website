lint:
	pylint --disable=bad-continuation,logging-fstring-interpolation,fixme,mixed-line-endings app tests

reformat:
	black --exclude=app/__init__.py app tests
	isort --recursive app tests

mypy:
	mypy --ignore-missing-imports app tests

jslint:
	jshint app/static/js/

stylechecks:
	make reformat 
	make lint
	make mypy
	make jslint

test:
	python -m pytest tests

compile-go:
	go build -buildmode=c-shared -o app/static/bin/projectEuler.so app/static/goCode/main.go