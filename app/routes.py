"""
The various routes for the webserver
"""

import json
import logging
from pathlib import Path
from typing import Dict

import markdown
from flask import render_template, request, send_from_directory
from flask.logging import create_logger
from flask.templating import render_template_string

from app import app
from app.constants import BLOG_POST_DIRECTORY, NOTEBOOK_DIRECTORY, STATIC_DIRECTORY
from gcp_util.secrets import (
    get_cron_verification_password,
    get_telegram_bot_key,
    get_telegram_user_id,
)
from telegram_bot.bot import handle_bot_request, send_message_to_me

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
        {"name": "Advent of Code", "route": "/advent_of_code"},
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


def generate_blog_post_from_markdown_file(static_file_location: Path) -> HTML:
    """
    Takes a markdown file and generates a HTML string from it
    """

    md_content = static_file_location.read_text()
    markdown_extension_configs = {"mdx_math": {"enable_dollar_delimiter": True}}
    md = markdown.Markdown(
        extensions=["nl2br", "mdx_math", "fenced_code", "meta"],
        extension_configs=markdown_extension_configs,
    )
    html = md.convert(md_content)
    blog_post = md.Meta
    blog_post['content'] = html

    return blog_post


@app.route("/blog")
def blog() -> HTML:
    """
    Renders the blog index page
    """
    blog_posts = []
    for blog_file in BLOG_POST_DIRECTORY.iterdir():
        blog_post = generate_blog_post_from_markdown_file(blog_file)
        blog_posts.append(blog_post)

    return extend_base_template("blog.html", blogPosts=blog_posts)


@app.route("/blog/<int:post_id>")
def blog_post(post_id: int) -> HTML:
    """
    Renders an individual page from the blog
    """

    for blog_file in BLOG_POST_DIRECTORY.iterdir():
        blog_post = generate_blog_post_from_markdown_file(blog_file)
        if blog_post["post_id"] == int(post_id):
            return extend_base_template("blog_post.html", blogPost=blog_post)
        
    return four_oh_four()


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

    html = generate_blog_post_from_markdown_file(STATIC_DIRECTORY / "changelog.md")
    return extend_base_template(html)

@app.route("/404")
def four_oh_four() -> HTML:
    """
    Custom 404 page
    """
    html = extend_base_template("404.html")


def _get_completed_and_half_completed_advent_of_code():
    completed_days = set()
    half_completed_days = set()

    for f in (STATIC_DIRECTORY / "code").iterdir():
        if str(f.parts[-1]).startswith("solution"):
            problem_number = int(f.parts[-1].split(".")[0].split("_")[1])
            if all(part in f.read_text() for part in ["part_1", "part_2"]):
                completed_days.add(problem_number)
            else:
                half_completed_days.add(problem_number)

    return {
        "completed_days": completed_days,
        "half_completed_days": half_completed_days,
    }


@app.route("/advent_of_code")
def advent_of_code() -> HTML:
    """
    Renders the advent of code page
    """
    completed_and_half_completed_days = (
        _get_completed_and_half_completed_advent_of_code()
    )
    completed_days = completed_and_half_completed_days["completed_days"]
    half_completed_days = completed_and_half_completed_days["half_completed_days"]

    return extend_base_template(
        "advent_of_code.html",
        completed_days=completed_days,
        half_completed_days=half_completed_days,
    )


@app.route("/get_advent_solution/<int:problem_number>")
def get_advent_solution(problem_number: int):
    """
    Endpoint to fetch the code for a day of advent of code
    """
    completed_and_half_completed_days = (
        _get_completed_and_half_completed_advent_of_code()
    )
    all_valid_days = (
        completed_and_half_completed_days["completed_days"]
        | completed_and_half_completed_days["half_completed_days"]
    )

    if problem_number not in all_valid_days:
        return f"// no solution for day {problem_number} yet"

    return (STATIC_DIRECTORY / f"code/solution_{problem_number}.rs").read_text()


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


@app.route("/robots.txt")
def robots():
    """
    Serve up the robots.txt file
    """
    return send_from_directory(STATIC_DIRECTORY, "robots.txt")


@app.route("/sitemap.xml")
def sitemap():
    """
    Serve up the sitemap
    """
    return send_from_directory(STATIC_DIRECTORY, "sitemap.xml")


@app.route("/web_ticker", methods=["POST"])
def web_ticker():
    """
    Route to receive and verify requests from my web-ticker
    cron job, which periodically pings this website
    """

    request_data = request.get_json()
    if not request_data["verify"] == get_cron_verification_password():
        return ""

    send_message_to_me("cron ping received")

    return ""
