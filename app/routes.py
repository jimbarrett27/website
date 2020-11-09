"""
The various routes for the webserver
"""

import json
import logging
import re

import markdown
from flask import render_template
from flask.logging import create_logger

from app import app
from ctypes import c_int64, cdll
from pathlib import Path
from typing import Dict

logging.basicConfig(level=logging.INFO)
LOGGER = create_logger(app)

STATIC_DIRECTORY = Path(__file__).parent.resolve() / "static"
BLOG_POST_DIRECTORY = STATIC_DIRECTORY / "blogPosts"
NOTEBOOK_DIRECTORY = STATIC_DIRECTORY / "jupyterHtml"

HTML = str

TAB_CONTENTS = [
    {"name": "Publications", "route": "/publications"},
    {"name": "Project Euler", "route": "/project_euler"},
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


@app.route("/project_euler")
def project_euler() -> HTML:
    """
    Works out which problems are solved and renders the project Euler page
    """

    solutions_directory = STATIC_DIRECTORY / "goCode/solutions"
    exercise_solution_files = solutions_directory.glob("*.go")

    # all solution files follow the pattern problem{}.go
    problems_json = STATIC_DIRECTORY / "data/projectEuler/projectEulerMetadata.json"
    problems_metadata = json.loads(problems_json.read_text())

    solved_problems = []
    for path in exercise_solution_files:
        matches = re.search(r"\d+", path.parts[-1])
        if matches is None:
            continue
        problem_number = int(matches.group())
        problem_metadata = [
            metadata
            for metadata in problems_metadata
            if metadata["number"] == problem_number
        ][0]
        problem_metadata["code"] = path.read_text()
        solved_problems.append(problem_metadata)

    return render_template(
        "projectEuler.html",
        solvedProblems=solved_problems,
        solvedProblemNumbers=[problem["number"] for problem in solved_problems],
        tab_contents=TAB_CONTENTS,
    )


@app.route("/project_euler_data/<int:problem_number>", methods=["GET"])
def fetch_project_euler_data(problem_number: int) -> str:
    """
    Fetchs the data file for project euler and serves it up.
    """
    LOGGER.info(f"Fetching the data file for exercise {problem_number}")
    data_dir = STATIC_DIRECTORY / f"data/projectEuler/problem{problem_number}.dat"
    return data_dir.read_text()


@app.route("/project_euler_solution_code/<int:problem_number>", methods=["GET"])
def fetch_project_euler_solution_code(problem_number: int) -> str:
    """
    Gets the code for the requested problem number

    # TODO show library functions as well as the solution itself
    """
    LOGGER.info(f"Fetching code for problem number {problem_number}")

    code_file = STATIC_DIRECTORY / "goCode/solutions" / f"problem{problem_number}.go"
    if code_file.exists() and code_file.is_file():
        return code_file.read_text()

    return f"No code found for problem {problem_number}"


@app.route("/project_euler_solution/<int:problem_number>", methods=["GET"])
def fetch_project_euler_solution(problem_number: int) -> str:
    """
    Send the generator reponse to poll for solutions
    """

    solutions_lib = cdll.LoadLibrary(str(STATIC_DIRECTORY / "bin/projectEuler.so"))
    solutions_lib.solution.restype = c_int64
    solution = solutions_lib.solution(int(problem_number))

    return str(solution)


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
        with open(post_location, "r") as f:
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
        if metadata['post_id'] == int(post_id):
            post_location = BLOG_POST_DIRECTORY / metadata["content_file"]
            with open(post_location, "r") as f:
                metadata["content"] = markdown.markdown(f.read(), extensions=["nl2br"])
            post_metadata = metadata

    return render_template("blog_post.html", blogPost=post_metadata, tab_contents=TAB_CONTENTS)


@app.route("/notebooks/<notebook_name>")
def notebook(notebook_name: str) -> HTML:
    """
    Renders a jupyter notebook as HTML
    """
    return (NOTEBOOK_DIRECTORY / f"{notebook_name}.html").read_text()
