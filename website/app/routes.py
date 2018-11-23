from app import app
from flask import render_template

@app.route('/')
@app.route('/index')
def index():
    user = {'username': 'Jim'}
    posts = [
        {
            'author': {'username': 'Jim1'},
            'body': 'Oh fuck!!'
        },
        {
            'author': {'username': 'Jim2'},
            'body': 'It works!!'
        }
    ]
    return render_template('index.html', title='Home', user=user, posts=posts)
