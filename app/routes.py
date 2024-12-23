"""
The various routes for the webserver
"""

import json
import logging
from functools import lru_cache
from pathlib import Path
import requests
from collections import defaultdict

import markdown
from flask import render_template, request, send_from_directory
from flask.logging import create_logger
from flask.templating import render_template_string

from app import app
from app.constants import BLOG_POST_DIRECTORY, NOTEBOOK_DIRECTORY, STATIC_DIRECTORY

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
        {"name": "Advent of Code", "route": "/advent_of_code"},
        {"name": "Publications", "route": "/publications"},
        {"name": "Blog", "route": "/blog"},
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


def generate_blog_post_from_markdown_file(static_file_location: Path) -> HTML:
    """
    Takes a markdown file and generates a HTML string from it
    """

    md_content = static_file_location.read_text()
    markdown_extension_configs = {"mdx_math": {"enable_dollar_delimiter": True}}
    md_converter = markdown.Markdown(
        extensions=["nl2br", "mdx_math", "fenced_code", "meta"],
        extension_configs=markdown_extension_configs,
    )
    html = md_converter.convert(md_content)
    # metadata allows multiple values per key, take the first one
    post = {k: v[0] for k, v in md_converter.Meta.items()}  # pylint: disable=no-member
    post["content"] = html

    return post


@app.route("/blog")
def blog() -> HTML:
    """
    Renders the blog index page
    """
    blog_posts = []
    for blog_file in BLOG_POST_DIRECTORY.iterdir():
        post = generate_blog_post_from_markdown_file(blog_file)
        blog_posts.append(post)

    blog_posts.sort(key=lambda post: int(post["post_id"]), reverse=True)

    return extend_base_template("blog.html", blogPosts=blog_posts)


@app.route("/blog/<int:post_id>")
def blog_post(post_id: int) -> HTML:
    """
    Renders an individual page from the blog
    """

    for blog_file in BLOG_POST_DIRECTORY.iterdir():
        post = generate_blog_post_from_markdown_file(blog_file)
        if int(post["post_id"]) == int(post_id):
            return extend_base_template("blog_post.html", blogPost=post)

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

    changelog_content = generate_blog_post_from_markdown_file(
        STATIC_DIRECTORY / "changelog.md"
    )
    return extend_base_template(changelog_content["content"])


@app.route("/404")
def four_oh_four() -> HTML:
    """
    Custom 404 page
    """
    return extend_base_template("404.html")


@lru_cache
def _get_solution_status_dict() -> dict[int, dict[int, str]]:


    solution_status_url = "https://raw.githubusercontent.com/jimbarrett27/AdventOfCode/refs/heads/main/solution_status.txt"
    solution_status = requests.get(solution_status_url).text

    solution_status_dict = defaultdict(dict)

    for line in solution_status.splitlines():
        year, day, part1, part2 = line.split()

        if part1 == "*" and part2 == "*":
            solution_status_dict[year][day] = "both"
        elif part1 == "*" or part2 == "*":
            solution_status_dict[year][day] = "half"
        else:
            solution_status_dict[year][day] = "neither"

    return solution_status_dict


@app.route("/advent_of_code")
def advent_of_code() -> HTML:
    """
    Renders the advent of code page
    """
    solution_status_dict = _get_solution_status_dict()

    return extend_base_template(
        "advent_of_code.html",
        solution_status_dict=solution_status_dict,
    )


@app.route("/get_advent_solution/<int:year>/<int:day>")
def get_advent_solution(year: int, day: int) -> str:
    """
    Endpoint to fetch the code for a day of advent of code
    """
    
    solution_url = f"https://raw.githubusercontent.com/jimbarrett27/AdventOfCode/refs/heads/main/{year}/ex_{day}.py"
    return requests.get(solution_url).text


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
