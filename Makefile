lint:
	pylint --disable=bad-continuation,fixme app twitter

reformat:
	black --exclude=app/__init__.py app twitter
	isort --recursive app twitter

mypy:
	mypy --ignore-missing-imports app twitter

jslint:
	npx eslint app/static/js/ 

stylechecks:
	make reformat 
	make lint
	make mypy
	make jslint