"""
The various routes for the webserver
"""

import json
import logging
from pathlib import Path
from typing import Dict

import markdown
from flask import render_template, request
from flask.logging import create_logger
from flask.templating import render_template_string

from app import app
from app.constants import BLOG_POST_DIRECTORY, NOTEBOOK_DIRECTORY, STATIC_DIRECTORY
from gcp_util.secrets import get_telegram_bot_key, get_telegram_user_id
from telegram_bot.bot import handle_bot_request

logging.basicConfig(level=logging.INFO)
LOGGER = create_logger(app)

HTML = str


def extend_base_template(*args, **kwargs):
    """
    Passes all of the kwargs required by the base template,
    then continues with rendering the template
    """

    tab_contents = [
        {"name": "Home", "route": "/"},
        {"name": "Publications", "route": "/publications"},
        {"name": "Blog", "route": "/blog"},
        {"name": "Changelog", "route": "/changelog"},
    ]

    if args[0].endswith(".html"):
        return render_template(*args, tab_contents=tab_contents, **kwargs)

    return render_template_string(*args, tab_contents=tab_contents, **kwargs)


@app.route("/")
def main() -> HTML:
    """
    Renders the base page
    """

    return extend_base_template("main.html")


@app.route("/publications")
def publications() -> HTML:
    """
    Renders the publications page
    """
    publications_json = STATIC_DIRECTORY / "data/activity/publications.json"

    return extend_base_template(
        "publications.html",
        publications=json.loads(publications_json.read_text()),
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

    md_content = static_file_location.read_text()
    html = markdown.markdown(md_content, extensions=["nl2br"])

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

    return extend_base_template("blog.html", blogPosts=blog_posts)


@app.route("/blog/<int:post_id>")
def blog_post(post_id: int) -> HTML:
    """
    Renders an individual page from the blog
    """

    post_metadata = {}
    for metadata in get_blog_metadata():
        if metadata["post_id"] == int(post_id):
            post_location = BLOG_POST_DIRECTORY / metadata["content_file"]
            metadata["content"] = generate_html_from_static_markdown(post_location)
            post_metadata = metadata

    return extend_base_template("blog_post.html", blogPost=post_metadata)


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

    html = generate_html_from_static_markdown(STATIC_DIRECTORY / "changelog.md")
    return extend_base_template(html)


@app.route("/telegram_webhook/<telegram_key>", methods=["POST"])
def telegram_webhook(telegram_key: str):
    """
    Simple hello world route to act as a webhook for my telegram bot.
    Simply echos the message I send it back to me
    """

    if not telegram_key == get_telegram_bot_key():
        return ""

    if not request.method == "POST":
        return ""

    request_data = request.get_json()
    message = request_data["message"]

    if not message["from"]["id"] == get_telegram_user_id():
        return ""

    handle_bot_request(message["text"].lower())

    return ""
