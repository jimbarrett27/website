title: Preprint Lunacy - Post 4
date: TODO
author: Jim Barrett
post_id: 10

This post relates to my preprint lunacy project. You can find the introduction post [here](https://jimbarrett.phd/blog/6). This post covers my progress up to commit TODO.

For the next step in building this thing, I want to sure up the repo a bit with some better practises, since I've been playing pretty fast and loose with coding style so far. I'm starting to get pretty excited about the prospect of getting recommended papers. There are a few steps between now and then, the rough plan is;

* Add functionality for favouriting papers
* Build a simple model or heuristic to find papers close to a set of papers
* Decide on some heuristic for papers being "close enough" to warrant a recommendation
* A page to present the recommendations

But, before all that fun stuff, time to eat my vegetables. My usual setup for quality control on a repo is formatting, linting and tests. I set up a CI/CD pipeline to run these for every pull request, and not allow merging without them passing. I also forbid pushing directly to the `main` branch.

In Python, I have typically used [isort](https://pycqa.github.io/isort/), [black](https://pypi.org/project/black/) and [pylint](https://pypi.org/project/pylint/). Since I'm using this project to learn some new stuff, I also want to try another code quality tool, namely [mypy](https://mypy-lang.org/).

Fortunately, I already have quite a bit of code and config I can reuse for this from other repos, so I can directly steal the `.isort.cfg` and `.pylintrc` files from other projects. Running isort and black just rearranges what's already there, so they were easy. Pylint throws up a bunch of complaints though, so I went through and fixed those one by one. Mypy was also reasonably straightforward to use, so I configured that, and added the various stub files it was asking for. I then set up a google coud build trigger to run all of these tests on PRs, and merged in my lovely clean codebase to check everything was working.

I always get a good feeling doing work like this, kind of like how I imagine craftsmen get from cleaning and organising all of their tools in their workshop. But, now that that's done, on to the really fun stuff.