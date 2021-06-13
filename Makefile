lint:
	pylint --disable=bad-continuation,logging-fstring-interpolation,fixme,mixed-line-endings app

reformat:
	black --exclude=app/__init__.py app 
	isort --recursive app 

mypy:
	mypy --ignore-missing-imports app


stylechecks:
	make reformat 
	make lint
	make mypy

