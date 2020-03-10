"""
The various routes for the webserver
"""

import json
import os
import re
from pathlib import Path
from typing import Dict
from ctypes import cdll, c_double

import markdown
import numpy as np
from flask import render_template, Response

from app import app

STATIC_DIRECTORY = Path(__file__).parent.resolve() / "static"
BLOG_POST_DIRECTORY = STATIC_DIRECTORY / "blogPosts"
NOTEBOOK_DIRECTORY = STATIC_DIRECTORY / "jupyterHtml"

HTML = str


from io import StringIO 
import sys

class Capturing(list):
    def __enter__(self):
        self._stdout = sys.stdout
        sys.stdout = self._stringio = StringIO()
        return self
    def __exit__(self, *args):
        self.extend(self._stringio.getvalue().splitlines())
        del self._stringio
        sys.stdout = self._stdout

@app.route("/")
def main() -> HTML:
    """
    Renders the base page
    """

    tab_contents = [
        {
            "name": "About",
            "variable_name": "about",
            "content": render_template("about.html"),
            "active": "active",
        },
        {
            "name": "Publications",
            "variable_name": "publications",
            "content": publications(),
            "active": "",
        },
        {
            "name": "Project Euler",
            "variable_name": "project_euler",
            "content": project_euler(),
            "active": "",
        },
        {"name": "Blog", "variable_name": "blog", "content": blog(), "active": ""},
    ]

    return render_template("main.html", tab_contents=tab_contents)


def publications() -> HTML:
    """
    Renders the publications page
    """
    publications_json = STATIC_DIRECTORY / "data/activity/publications.json"

    return render_template(
        "publications.html", publications=json.loads(publications_json.read_text())
    )


@app.route("/project_euler_solution_code/<problem_number>", methods=['GET'])
def fetch_project_euler_solution_code(problem_number: int) -> str:
    code_file = STATIC_DIRECTORY / "goCode/solutions" / f"problem{problem_number}.go"
    return code_file.read_text()

@app.route("/project_euler_solution/<problem_number>", methods=['GET'])
def fetch_project_euler_solution(problem_number: int) -> str:
    solutions_lib = cdll.LoadLibrary(STATIC_DIRECTORY / 'bin/projectEuler.so')
    solutions_lib.solution.restype = c_double
    solution = solutions_lib.solution(int(problem_number))
    if solution == -1:
        return f"No Solution for problem {problem_number}"
    if solution == round(solution):
        solution = int(solution)
    return str(solution)

def project_euler() -> HTML:
    """
    Works out which problems are solved and renders the project Euler page
    """

    solutions_directory = STATIC_DIRECTORY / "goCode/solutions"
    exercise_solution_files = solutions_directory.glob('*.go')

    # all solution files follow the pattern problem{}.go
    problems_json = STATIC_DIRECTORY / "data/projectEuler/projectEulerMetadata.json"
    problems_metadata = json.loads(problems_json.read_text())

    solved_problems = []
    for path in exercise_solution_files:
        problem_number = int(re.search(r'\d+', path.parts[-1]).group())
        problem_metadata = [metadata for metadata in problems_metadata if metadata['number'] == problem_number][0]
        problem_metadata['code'] = path.read_text()
        solved_problems.append(problem_metadata)

    return render_template(
        "projectEuler.html",
        solvedProblems=solved_problems,
        solvedProblemNumbers=[problem['number'] for problem in solved_problems]
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
