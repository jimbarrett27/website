lint:
	pylint app twitter

reformat:
	black app twitter
	isort --recursive app twitter

mypy:
	mypy app twitter

stylechecks:
	make reformat 
	make lint 
	make mypy