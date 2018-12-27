from app import app
from flask import render_template

@app.route('/')
@app.route('/frontPage')
def frontPage():
    return render_template('frontPage.html')

@app.route('/activity')
def activity():
	return render_template('activity.html')

@app.route('/projectEuler')
def projectEuler():

	solved_problems = [1,2,3,4,5,6]

	return render_template('projectEuler.html', solved_problems=solved_problems)
