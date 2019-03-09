import json
import markdown
import os

from app import app
from collections import namedtuple
from flask import render_template, abort
from pathlib import Path

STATIC_DIRECTORY = os.path.join(os.path.realpath(os.path.dirname(__file__)), 'static')
BLOG_POST_DIRECTORY = os.path.join(STATIC_DIRECTORY, 'blogPosts')
NOTEBOOK_DIRECTORY = os.path.join(STATIC_DIRECTORY, 'jupyterHtml')

def getBlogMetadata():
	with open(os.path.join(BLOG_POST_DIRECTORY, 'blogMetadata.json')) as f:
		return json.load(f)


@app.route('/')
@app.route('/frontPage')
def frontPage():
    return render_template('frontPage.html')

@app.route('/activity')
def activity():

	with open(os.path.join(STATIC_DIRECTORY, 'data', 'activity', 'publications.json')) as f:
		publications = json.load(f)

	return render_template('activity.html', publications=publications)

@app.route('/projectEuler')
def projectEuler():

	solved_problems = [1,2,3,4,5,6,7,8,9,10,11]

	return render_template('projectEuler.html', solved_problems=solved_problems)

@app.route('/blog')
def blog():

	blogMetadata = getBlogMetadata()	

	blogPosts = []
	for metadata in blogMetadata:
		postLocation = os.path.join(BLOG_POST_DIRECTORY, metadata['content_file'])
		with open(postLocation, 'r') as f:
			metadata['content'] = markdown.markdown(f.read(), extensions=['nl2br'])
		blogPosts.append(metadata)

	return render_template('blog.html', blogPosts=blogPosts)

@app.route('/blog/<postHandle>')
def post(postHandle):

	blogMetadata = getBlogMetadata()
	
	for metadata in blogMetadata:
		if metadata['content_file'][:-3] == postHandle:
			postLocation = os.path.join(BLOG_POST_DIRECTORY, metadata['content_file'])
			with open(postLocation, 'r') as f:
				metadata['content'] = markdown.markdown(f.read(), extensions=['nl2br'])
			return render_template('blogPost.html', post=metadata)

	abort(404)

@app.route('/notebooks/<notebookName>')
def notebook(notebookName):	
	with open(os.path.join(NOTEBOOK_DIRECTORY, f'{notebookName}.html')) as f:
		return f.read()

