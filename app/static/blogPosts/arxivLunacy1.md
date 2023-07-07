This post relates to my arXiv lunacy project. You can find the introduction post [here](https://jimbarrett.phd/blog/6). This post covers my progress up to commit [#fd091c1](https://github.com/jimbarrett27/arxiv-lunacy/commit/fd091c1d737ef458145dbd2b40408ba600d2bd5f).

In this post I cover the simple MVP I have built for finding the N papers most similar to a paper input by the user.

The first thing I needed to do was to get some data. Fortunately, arXiv themselves [provide a dataset](https://www.kaggle.com/datasets/Cornell-University/arxiv) vis Kaggle of all of the information I expect I will ever need for bootstrapping my model with all the papers up until now. In particular, they provide the title, arxiv-id, categories and abstract of all preprints hosted on the arxiv. I downloaded the data, which is provided in JSONL format, and wrote a small function to serve up the papers with categories I'm personally interested in; 

<!-- <pre><code class="language-python" style="text-align: left;">
def records_gen() -> Generator[Dict[str,Any]]:
    """
    Generate the relevant records
    """
    with Path('arxiv-metadata-oai-snapshot.json').open('r') as f:
        for line in f:
            record = json.loads(line)
            cats = set(record['categories'].split())
            if len(cats & INTERESTING_ARXIV_CATEGORIES) == 0:
                continue

            yield record
</code></pre> -->

```python
def records_gen() -> Generator[Dict[str,Any]]:
    """
    Generate the relevant records
    """
    with Path('arxiv-metadata-oai-snapshot.json').open('r') as f:
        for line in f:
            record = json.loads(line)
            cats = set(record['categories'].split())
            if len(cats & INTERESTING_ARXIV_CATEGORIES) == 0:
                continue

            yield record
```