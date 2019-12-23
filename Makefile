lint:
	pylint --disable=bad-continuation,fixme app twitter crypto

reformat:
	black --exclude=app/__init__.py app twitter crypto
	isort --recursive app twitter crypto

mypy:
	mypy --ignore-missing-imports app twitter crypto

jslint:
	npx eslint app/static/js/ 

stylechecks:
	make reformat 
	make lint
	make mypy
	make jslint
