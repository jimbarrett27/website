import json
import os

from app import app
from flask import render_template
from pathlib import Path

BASE_DIRECTORY = os.path.realpath(os.path.dirname(__file__))

@app.route('/')
@app.route('/frontPage')
def frontPage():
    return render_template('frontPage.html')

@app.route('/activity')
def activity():

	with open(os.path.join(BASE_DIRECTORY,'static', 'data', 'activity', 'publications.json')) as f:
		publications = json.load(f)

	return render_template('activity.html', publications=publications)

@app.route('/projectEuler')
def projectEuler():

	solved_problems = [1,2,3,4,5,6,7,8,9,10,11]

	return render_template('projectEuler.html', solved_problems=solved_problems)

@app.route('/blog/<postName>')
def post(postName):

	post = {}

	return render_template('blogPost.html', post=post)

