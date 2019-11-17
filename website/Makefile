lint:
	pylint --disable=bad-continuation,fixme app twitter

reformat:
	black --exclude=__init__.py app twitter
	isort --recursive app twitter

mypy:
	mypy app twitter

stylechecks:
	make reformat 
	make lint
	make mypy