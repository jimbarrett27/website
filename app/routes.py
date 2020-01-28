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

STATIC_DIRECTORY = Path(__file__).parent.resolve() / 'static'
BLOG_POST_DIRECTORY = STATIC_DIRECTORY / 'blogPosts'
NOTEBOOK_DIRECTORY = STATIC_DIRECTORY / 'jupyterHtml'

HTML = str

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
    publications_json = STATIC_DIRECTORY / "data/activity/publications.json"
    publications = json.loads(publications_json.read_text())

    return render_template("publications.html", publications=publications)


def project_euler() -> HTML:
    """
    Works out which problems are solved and renders the project Euler page
    """

    solutions_directory = STATIC_DIRECTORY / "js/exerciseSolutions"
    exercise_solution_files = os.listdir(solutions_directory)

    # all solution files follow the pattern exercise{}.js
    solved_problem_numbers = np.sort(
        [
            int(filename[8:-3])
            for filename in exercise_solution_files
            if filename.endswith(".js")
        ]
    )

    problems_json = STATIC_DIRECTORY / "data/projectEuler/projectEulerMetadata.json"
    problems_metadata = json.loads(problems_json.read_text())

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


def get_blog_metadata() -> Dict:
    """
    grabs the static metadata file for blogs
    """
    return json.loads((BLOG_POST_DIRECTORY / "blogMetadata.json").read_text())

def blog() -> HTML:
    """
    Renders the blog index page
    """

    blog_metadata = get_blog_metadata()

    blog_posts = []
    for metadata in blog_metadata:
        post_location = BLOG_POST_DIRECTORY / metadata["content_file"]
        with open(post_location, "r") as f:
            metadata["content"] = markdown.markdown(f.read(), extensions=["nl2br"])
        blog_posts.append(metadata)

    return render_template("blog.html", blogPosts=blog_posts)


@app.route("/notebooks/<notebook_name>")
def notebook(notebook_name: str) -> HTML:
    """
    Renders a jupyter notebook as HTML
    """
    return (NOTEBOOK_DIRECTORY / f"{notebook_name}.html").read_text()
