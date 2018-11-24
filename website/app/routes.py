from app import app
from flask import render_template

@app.route('/')
def frontPage():
    return render_template('frontPage.html')

@app.route('/activity')
def activity():
	return render_template('activity.html')
