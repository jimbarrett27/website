import os

os.system("black app")
os.system("isort app")
os.system("python -m pylint app")
