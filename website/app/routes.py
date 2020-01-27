"""
The various routes for the webserver
"""

import json
import os
from typing import Dict

import markdown
import numpy as np
from flask import abort, render_template

from app import app
from pathlib import Path

STATIC_DIRECTORY = os.path.join(os.path.realpath(os.path.dirname(__file__)), "static")
BLOG_POST_DIRECTORY = os.path.join(STATIC_DIRECTORY, "blogPosts")
NOTEBOOK_DIRECTORY = os.path.join(STATIC_DIRECTORY, "jupyterHtml")

HTML = str


def get_blog_metadata() -> Dict:
    """
    grabs the static metadata file for blogs
    """
    with open(os.path.join(BLOG_POST_DIRECTORY, "blogMetadata.json")) as f:
        return json.load(f)


@app.route("/")
def main() -> HTML:
    """
    Renders the base page
    """

    tab_contents = [
        {
            "name": 'About',
            "variable_name": 'about',
            "content": render_template("about.html"),
            "active": "active"
        },
        {
            "name": 'Publications',
            "variable_name": 'publications',
            "content": publications(),
            "active": ""
        },
        {
            "name": "Project Euler",
            "variable_name": "project_euler",
            "content": project_euler(),
            "active": ""
        },
        {
            "name": "Blog",
            "variable_name": "blog",
            "content": blog(),
            "active": ""
        }
    ]

    return render_template("main.html", tab_contents=tab_contents)


def publications() -> HTML:
    """
    Renders the publications page
    """
    with open(
        os.path.join(STATIC_DIRECTORY, "data", "activity", "publications.json")
    ) as f:
        publications = json.load(f)

    return render_template("publications.html", publications=publications)


def project_euler() -> HTML:
    """
    Works out which problems are solved and renders the project Euler page
    """

    solutions_directory = os.path.join(STATIC_DIRECTORY, "js", "exerciseSolutions")
    exercise_solution_files = os.listdir(solutions_directory)

    # all solution files follow the pattern exercise{}.js
    solved_problem_numbers = np.sort(
        [
            int(filename[8:-3])
            for filename in exercise_solution_files
            if filename.endswith(".js")
        ]
    )

    with open(
        os.path.join(
            STATIC_DIRECTORY, "data", "projectEuler", "projectEulerMetadata.json"
        )
    ) as f:
        problems_metadata = json.load(f)

    solved_problems = [
        problem
        for problem in problems_metadata
        if int(problem["number"]) in solved_problem_numbers
    ]

    return render_template(
        "projectEuler.html",
        solvedProblems=solved_problems,
        solvedProblemNumbers=solved_problem_numbers,
    )


def blog() -> HTML:
    """
    Renders the blog index page
    """

    blog_metadata = get_blog_metadata()

    blog_posts = []
    for metadata in blog_metadata:
        post_location = os.path.join(BLOG_POST_DIRECTORY, metadata["content_file"])
        with open(post_location, "r") as f:
            metadata["content"] = markdown.markdown(f.read(), extensions=["nl2br"])
        blog_posts.append(metadata)

    return render_template("blog.html", blogPosts=blog_posts)


@app.route("/blog/<post_handle>")
def post(post_handle: str) -> HTML:
    """
    Renders an individual blog page
    """

    blog_metadata = get_blog_metadata()

    for metadata in blog_metadata:
        if metadata["content_file"][:-3] == post_handle:
            post_location = os.path.join(BLOG_POST_DIRECTORY, metadata["content_file"])
            with open(post_location, "r") as f:
                metadata["content"] = markdown.markdown(f.read(), extensions=["nl2br"])
            return render_template("blogPost.html", post=metadata)

    abort(404)
    # TODO custom 404
    return ""


@app.route("/notebooks/<notebookName>")
def notebook(notebook_name: str) -> HTML:
    """
    Renders a jupyter notebook as HTML
    """
    with open(os.path.join(NOTEBOOK_DIRECTORY, f"{notebook_name}.html")) as f:
        return f.read()
