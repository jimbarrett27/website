---
title:  Preprint Lunacy - Post 1
description: ''
pubDate: '08 Jul 2023'
heroImage: '/blog-placeholder-3.jpg'
---

This post relates to my arXiv lunacy project. You can find the introduction post [here](https://jimbarrett.phd/blog/6). This post covers my progress up to commit [#fd091c1](https://github.com/jimbarrett27/arxiv-lunacy/commit/fd091c1d737ef458145dbd2b40408ba600d2bd5f).

In this post I cover the simple MVP I have built for finding the N papers most similar to a paper input by the user.

The first thing I needed to do was to get some data. Fortunately, arXiv themselves [provide a dataset](https://www.kaggle.com/datasets/Cornell-University/arxiv) vis Kaggle of all of the information I expect I will ever need for bootstrapping my model with all the papers up until now. In particular, they provide the title, arxiv-id, categories and abstract of all preprints hosted on the arxiv. I downloaded the data, which is provided in JSONL format, and wrote a small function to serve up the papers with categories I'm personally interested in (here stored in a constant set); 

```python
ARXIV_METADATA_SNAPSHOT_FILE =  Path('./arxiv-metadata-oai-snapshot.json')

def records_gen() -> Generator[Dict[str,Any], None, None]:
    """
    Generate the relevant records```
    """
    with Path(ARXIV_METADATA_SNAPSHOT_FILE).open('r') as f:
        for line in f:
            record = json.loads(line)
            cats = set(record['categories'].split())
            if len(cats & INTERESTING_ARXIV_CATEGORIES) == 0:
                continue

            yield record
```

I decided to use a transformer model to produce embeddings of the abstracts, and chose the [most popular sentence embedding model](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2) from Huggingface for my MVP. It does say in the model description that the model is only designed for texts up to 256 word pieces, so we can undoubtedly do better at some point, but for now it's good enough. I did look into using one of Google's cloud based models for sentence embedding, but a back of the envelope calculation suggested it would be approximately $30 to produce the initial embeddings. I might do this at some point, but not for now. I train the model thus;

```python

MODEL_NAME = 'sentence-transformers/all-MiniLM-L6-v2'
TORCH_DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

def produce_embeddings_df() -> pd.DataFrame:
    """
    Produce a dataframe of embeddings
    """

    # calculates how many relevant papers there are, simply for the progress bar
    n_records = get_number_of_records()

    ids = []
    embeddings = []

    model = SentenceTransformer(MODEL_NAME)

    for record in tqdm(records_gen(), total=n_records):
        ids.append(record['id'])
        embeddings.append(model.encode(record['abstract'], device=TORCH_DEVICE))

    embeddings_df = pd.DataFrame(embeddings)
    embeddings_df = embeddings_df.rename(columns={i:f"dim{i}" for i in embeddings_df.columns})
    embeddings_df["id"] = ids

    return embeddings_df

```

This took about an hour running on my modest gaming PC to embed the ~250k papers in the categories relevant to me, producing a file just over 400MB when saved to the `feather` format. Depending on how I ultimately end up deploying the model, this might be a bit cumbersome, but that's a problem for another day.

Finally, I wrote some functionality for finding the N papers most similar to a given paper. I implemented the cosine similarity as my comparison metric, which I think is a sensible choice for this problem. I might look into other, more "search engine"-y techniques if I feel I need it, but with some `numpy` magic, it's pretty trivial and fast to compute.

```python

def cosine_similarity(all_embeddings,embeddings_to_compare):
    
    numerators = np.dot(all_embeddings, embeddings_to_compare)
    denominators = (np.linalg.norm(all_embeddings)*np.linalg.norm(embeddings_to_compare))

    return numerators / denominators

```

And then finally we can compute the closest papers.

```python

def get_closest_papers(paper_ids, top_n = 10):
    
    embeddings_df = get_embeddings_df()
    id_to_index = get_paper_id_to_index(embeddings_df)
    paper_inds = [id_to_index[paper_id] for paper_id in paper_ids]
    
    ids = embeddings_df.id.to_numpy()
    embeddings_df = embeddings_df.drop(columns="id")
    paper_embeddings = embeddings_df.loc[paper_inds].to_numpy()
    other_embeddings = embeddings_df.to_numpy()
    
    cosine_sims = cosine_similarity(other_embeddings, paper_embeddings.T)
    
    top_n_inds = np.argpartition(cosine_sims, -top_n, axis=0)[-top_n:]
    
    return ids[top_n_inds]

```

An annoying amount of this code is just rearranging the data from how I have it stored, so I might look to improve that at some point, but for now it only takes a second or so to produce all the cosine similarities and provide the top N, which is pretty good!

The final thing to test is whether or not it actually works! I googled to find a paper broadly related to my current field of work, and found the paper *[Multi-Task Learning for Extraction of Adverse Drug Reaction Mentions from Tweets](https://arxiv.org/abs/1802.05130)*. I passed this into my similarity function and asked for the top 3 (well, top 4, since the paper always returns itself as a top match, which is good for a sanity check!). These were the papers it gave me back;

* [Semi-Supervised Recurrent Neural Network for Adverse Drug Reaction Mention Extraction](https://arxiv.org/abs/1709.01687)
* [Co-training for Extraction of Adverse Drug Reaction Mentions from Tweets](https://arxiv.org/abs/1802.05121)
* [Multi-Task Pharmacovigilance Mining from Social Media Posts](https://arxiv.org/abs/1801.06294)

Really cool! It seems to be working great! We'll have to see what more we can do with it in the next post!
