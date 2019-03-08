import json
import markdown
import os

from app import app
from collections import namedtuple
from flask import render_template
from pathlib import Path

STATIC_DIRECTORY = os.path.join(os.path.realpath(os.path.dirname(__file__)), 'static')

def getBlogPosts():

	blogDirectory = os.path.join(STATIC_DIRECTORY, 'blogPosts')

	blogPosts = []
	for postFile in os.listdir(blogDirectory):
		
		if not postFile.endswith('.md'):
			continue

		blogPost = {
			'content': ''
		}
		with open(os.path.join(blogDirectory, postFile)) as f:
			metadata_finished = False
			for line in f:
				# drop newline
				line = line[:-1]

				if line == 'metadata-finished':
					metadata_finished = True

				elif not metadata_finished:
					key, value = line.split(':')
					blogPost[key] = value

				else:
					blogPost['content'] += line

		blogPost['content'] = markdown.markdown(blogPost['content'])
		blogPosts.append(blogPost)

	return blogPosts


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

	blogPosts = getBlogPosts()

	return render_template('blog.html', blogPosts=blogPosts)

@app.route('/blog/<postName>')
def post(postName):

	with open(os.path.join(STATIC_DIRECTORY, 'blogPosts', 'test.md')) as f:
		md = f.read()
	post = markdown.markdown(md)
	return render_template('blogPost.html', post=post)

