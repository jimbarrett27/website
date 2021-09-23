"""
The various routes for the webserver
"""

import json
import logging
from typing import Dict
from pathlib import Path
from flask.templating import render_template_string

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
    {"name": "Changelog", "route": "/changelog"}
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

def generate_html_from_static_markdown(static_file_location: Path) -> HTML:
    """
    Takes a markdown file and generates a HTML string from it
    """

    md = static_file_location.read_text()
    html = markdown.markdown(md, extensions=["nl2br"])

    return html

@app.route("/blog")
def blog() -> HTML:
    """
    Renders the blog index page
    """

    blog_metadata = get_blog_metadata()

    blog_posts = []
    for metadata in blog_metadata:
        post_location = BLOG_POST_DIRECTORY / metadata["content_file"]
        metadata["content"] = generate_html_from_static_markdown(post_location)
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
            metadata["content"] = generate_html_from_static_markdown(post_location)
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

@app.route("/changelog")
def changelog() -> HTML:
    """
    Renders the changelog page
    """

    html = generate_html_from_static_markdown(STATIC_DIRECTORY / 'changelog.md')
    return render_template_string(html, tab_contents=TAB_CONTENTS)
