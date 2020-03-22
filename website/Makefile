lint:
	pylint --disable=bad-continuation,fixme app

reformat:
	black --exclude=app/__init__.py app
	isort --recursive app

mypy:
	mypy --ignore-missing-imports app

jslint:
	jshint app/static/js/

stylechecks:
	make reformat 
	make lint
	make mypy
	make jslint

compile-go:
	go build -buildmode=c-shared -o app/static/bin/projectEuler.so app/static/goCode/main.go