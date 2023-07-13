This post relates to my arXiv lunacy project. You can find the introduction post [here](https://jimbarrett.phd/blog/6). This post covers my progress up to commit [#ec11477](https://github.com/jimbarrett27/arxiv-lunacy/commit/ec114777cfb5da2f6d79e965105c67e353a134ab).

I feel like the next step in development of the project should be to implement functionality to be able to add new embeddings to my dataset. This will be necessary when fetching the latest preprints, screening them for papers which might be interesting to me and then saving them for future reference.

It feels like I should probably be using a relational database or something similar in order to store the embeddings and update them. Honestly though, since this app is in all likelihood only going to be used by me, I don't really care about a few seconds of latency. Instead, I will opt for simply storing the tables I produce as blobs in container storage, then download them and load them into pandas when I need them. I will try and design the schema of the tables such that I could theoretically transform things over to a relational database if I ever need to. 

I have mostly developed my personal projects on Google Cloud, and I will do the same here. The plan is that I will put the `feather` encoded table of embeddings into blob storage into a Google Cloud Storage bucket. I happen to already have some code in the backend of this website (where you're reading this blog) which solves some of these problems. One day I might look into a good way of separating out some of these general purpose utilities I write between projects and making them available across all my projects (by having my own package index or something), but for now I will shamelessly copy-paste and modify the code for the new use case.

After wrestling a little bit with getting Google authentication working reliably locally, and then spending even longer overcomplicating my solution using various `io` tricks with GCP's own Python tools, I discovered the wonderful, if slightly opaquely named, library `gcsfs`. With this, I was able to write the code to both load and dump dataframes to GCP storage buckets;

<pre><code class="language-python" style="text-align: left;">

import pandas as pd

from util.constants import GCP_BUCKET_NAME

def get_blob_stored_dataframe(blob_name: str):
    """
    Retrieves and deserialises a blob stored at blob_name
    """
    df = pd.read_feather(f'gs://{GCP_BUCKET_NAME}/{blob_name}')

    return df


def save_dataframe_to_blob(
    df: pd.DataFrame, blob_name: str
) -> bool:
    """
    Appends the "update dict" to the json list stored at blob_name
    """

    df.to_feather(f'gs://{GCP_BUCKET_NAME}/{blob_name}')

    return False

</code></pre>

We'll wait and see if this method is fast enough to work for when I start writing functionality using the dataframe, but for now I feel I can work with it.

The next step is to start regularly embedding any new papers and adding them to the dataframe. I fiddled around for a while trying to figure out the arxiv API to search for papers and abstracts, but then figured that a better approach would be to instead listen to RSS feed, which posts the metadata about all the papers released each day. One problem I foresaw with this approach is that there will inevitably be a few days gap between the embeddings I produced initially from the monthly data dump to Kaggle, and the first time I start adding data from the RSS feed. However, I figured this is a problem easily fixed in the future by waiting a month or two, and then merging in whatever I'm missing from a future monthly Kaggle dump.

I started by writing a function which reads the IDs and abstracts from the RSS feed into a format I can work with. I tried parsing the feed by hand for a while using the Python standard XML parsing library, but it quickly became evident that it would be much easier to have the `feedreader` package handle everything for me. I then noticed that the abstracts were HTML formatted, and so I found the simple `html2text` tool to parse things like `<p>` tags into whitespace. The function ultimately looked like this;

<pre><code class="language-python" style="text-align: left;">

from util.constants import INTERESTING_ARXIV_CATEGORIES
import feedparser
from html2text import html2text

def get_arxiv_rss_url(arxiv_category: str):

    return f"http://export.arxiv.org/rss/{arxiv_category}"

def get_latest_ids_and_abstracts():

    paper_id_to_abstract = {}
    for category in INTERESTING_ARXIV_CATEGORIES:

        url = get_arxiv_rss_url(category)
        rss_content = feedparser.parse(url)
        for entry in rss_content['entries']:
            paper_id = entry['id'].split('/')[-1]
            paper_id_to_abstract[paper_id] = html2text(entry['summary'])

    return paper_id_to_abstract

</code></pre>

Now, to embed them, we simply use the same libraries and code as we did for the inital embedding. I did a bit of refactoring to the original script to pull this functionality into a common place. At this point, I'm not especially happy with the structure of the repo. I'm hoping that when it matures a bit a more logical arrangement of the code will become obvious. In any case, the embedding code looks like so;

<pre><code class="language-python" style="text-align: left;">

def get_latest_embedding_df():

    paper_id_to_abstract = get_latest_ids_and_abstracts()

    paper_ids = []
    embeddings = []
    for paper_id, abstract in paper_id_to_abstract.items():

        paper_ids.append(str(paper_id))
        embeddings.append(embed_abstract(abstract))

    embeddings = np.array(embeddings).squeeze()
    embeddings_df = pd.DataFrame(embeddings)
    # feather doesn't like numerical column names
    embeddings_df = embeddings_df.rename(columns={i:f"dim{i}" for i in embeddings_df.columns})
    embeddings_df["id"] = paper_ids

    return embeddings_df

</code></pre>

The final thing I want to set up in this post is the running of the code at regular intervals. I considered for a while putting an endpoint on this website, which tends to operate as my general purpose "always-on" machine. But I know that's not the best practice, and I want to start getting a bit better at the cloud infrastructure.

Ultimately, what I want is an ocassional, short running, scheduled job. It seems to me that the best solution will be a GCP "cloud function", in combination with the cloud scheduler to trigger it daily. Walking through the wizard for creating a cloud function, it looks as though for a non trivial function (beyond a few lines of code), the easiest thing to do is the package up a zip file with the relevant code and requirements and then put it somewhere on cloud storage. The entrypoint function has to be in a `main.py` file, it has to include a `requirements.txt` and then it needs to include whatever other code we need.

I don't really like the idea of cobbling together the relevant code every time I want to update the function, so I figured I'd try and write a script to put together the relevant files and zip them up. This was the script I came up with;

<pre><code class="language-python" style="text-align: left;">

import shutil
import tempfile as tmp
import zipfile
from pathlib import Path

import functions_framework
import pandas as pd

from arxiv_lunacy.embeddings import get_embeddings_df
from arxiv_lunacy.latest_papers import get_latest_embedding_df
from util.constants import (EMBEDDINGS_DF_FILENAME, GCP_FUNCTION_ZIPFILE_NAME,
                            REPO_ROOT)
from util.storage import save_dataframe_to_blob, save_file_to_blob


@functions_framework.http
def update_embeddings_df(_):

    current_embeddings_df = get_embeddings_df()
    embedding_update_df = get_latest_embedding_df()

    all_embeddings_df = pd.concat([current_embeddings_df, embedding_update_df])
    all_embeddings_df = all_embeddings_df.drop_duplicates(subset='id').reset_index().drop(columns='index')
    save_dataframe_to_blob(all_embeddings_df, EMBEDDINGS_DF_FILENAME)

    return '{"status":"200", "data": "OK"}' 


def create_and_upload_gcp_function_zipfile():

    tmpdir = Path(tmp.mkdtemp())

    zipfile_path = tmpdir / GCP_FUNCTION_ZIPFILE_NAME

    zf = zipfile.ZipFile(zipfile_path, 'w', zipfile.ZIP_DEFLATED)

        # upload the relevant code directories
    for dir in ['arxiv_lunacy', 'util']:
        for f in (REPO_ROOT / dir).iterdir():
            if not str(f).endswith('.py'):
                continue
            zf.write(str(f), f'{dir}/{f.name}')
    
    zf.write(REPO_ROOT / 'requirements.txt', 'requirements.txt')
    zf.write(REPO_ROOT / 'scripts/produce_gcp_functions.py', 'main.py')
    zf.close()

    save_file_to_blob(zipfile_path)
    shutil.rmtree(tmpdir)


if __name__ == '__main__':

    create_and_upload_gcp_function_zipfile()
        
</code></pre>

It took a few attempts to get it right. The main problems I ran into were making sure that the entrypoint function actually returned something (I have no idea if the JSON repsonse is necessary, but if it ain't broke, don't fix it), and making sure that the cloud scheduler has sufficient permissions to make the HTTP request to trigger the function. The function seems to take around a minute to execute (which might reduce if it's clever about caching the SentenceTransformer model). I will monitor it over the next few days, but for now it seems like a success!

Next step: a frontend.