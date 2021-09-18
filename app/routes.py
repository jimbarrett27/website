"""
The various routes for the webserver
"""

import json
import logging
from typing import Dict

import markdown
from flask import render_template
from flask.logging import create_logger

from app import app
from app.constants import BLOG_POST_DIRECTORY, NOTEBOOK_DIRECTORY, STATIC_DIRECTORY

logging.basicConfig(level=logging.INFO)
LOGGER = create_logger(app)

HTML = str

TAB_CONTENTS = [
    {"name": "Home", "route": "/"},
    {"name": "Publications", "route": "/publications"},
    {"name": "Blog", "route": "/blog"},
]


@app.route("/")
def main() -> HTML:
    """
    Renders the base page
    """

    return render_template("main.html", tab_contents=TAB_CONTENTS)


@app.route("/publications")
def publications() -> HTML:
    """
    Renders the publications page
    """
    publications_json = STATIC_DIRECTORY / "data/activity/publications.json"

    return render_template(
        "publications.html",
        publications=json.loads(publications_json.read_text()),
        tab_contents=TAB_CONTENTS,
    )


def get_blog_metadata() -> Dict:
    """
    grabs the static metadata file for blogs
    """
    return json.loads((BLOG_POST_DIRECTORY / "blogMetadata.json").read_text())


@app.route("/blog")
def blog() -> HTML:
    """
    Renders the blog index page
    """

    blog_metadata = get_blog_metadata()

    blog_posts = []
    for metadata in blog_metadata:
        post_location = BLOG_POST_DIRECTORY / metadata["content_file"]
        with post_location.open("r") as f:
            metadata["content"] = markdown.markdown(f.read(), extensions=["nl2br"])
        blog_posts.append(metadata)

    return render_template("blog.html", blogPosts=blog_posts, tab_contents=TAB_CONTENTS)


@app.route("/blog/<int:post_id>")
def blog_post(post_id: int) -> HTML:
    """
    Renders an individual page from the blog
    """

    print(post_id)

    post_metadata = {}
    for metadata in get_blog_metadata():
        if metadata["post_id"] == int(post_id):
            post_location = BLOG_POST_DIRECTORY / metadata["content_file"]
            with post_location.open("r") as f:
                metadata["content"] = markdown.markdown(f.read(), extensions=["nl2br"])
            post_metadata = metadata

    return render_template(
        "blog_post.html", blogPost=post_metadata, tab_contents=TAB_CONTENTS
    )


@app.route("/notebooks/<notebook_file>")
def notebook(notebook_file: str) -> HTML:
    """
    Renders a jupyter notebook as HTML
    """
    return (NOTEBOOK_DIRECTORY / f"{notebook_file}").read_text()
