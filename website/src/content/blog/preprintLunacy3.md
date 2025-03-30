---
title:  Preprint Lunacy - Post 3
description: ''
pubDate: '19 Jul 2023'
heroImage: '/blog-placeholder-3.jpg'
---

This post relates to my preprint lunacy project. You can find the introduction post [here](https://jimbarrett.phd/blog/6). This post covers my progress up to commit [#d3917b6](https://github.com/jimbarrett27/arxiv-lunacy/commit/d3917b6c95cb201ad7a7b45eced72693d1e2e12c).

The next item on the agenda is a frontend. I might be being a bit too ambitious, but I've been intending to learn ReactJS for a long time, and now feels like the perfect opportunity to do so. In this post I'm going to try and put together a simple web interface making use of the work I've done so far. I'll make the backend with Flask, since that's something I'm already very familiar with, and I'll try and make the frontend with React. I'm reserving the right to bail out and revert to Jinja2 at some point during this post 😇.

So, my wishlist for this post will be the following;

* A search bar where I can input search terms
* A backend which embeds the search term and returns the best matching papers
* A display which shows the title, authors and abstract of the best matching papers

Hopefully this will then act as a base for future features I want to add, whilst being sufficiently simple to facilitate my learning of React.

I started by reading [this tutorial](https://blog.miguelgrinberg.com/post/how-to-create-a-react--flask-project) for setting up a Flask + React project. It looks as though there is no problem with developing the frontend first with some dummy data, and then worry about the backend and calling into it later. I therefore hopped over to reading the tutorials on the [react homepage](https://react.dev/).

The recommendation in the react tutorials was to build a static version of your page before trying to add in the dynamic content. I thought about how to naturally break down the MVP into components, and came up with the following;

```javascript
const PAPERS = [{
  "title": "A title",
  "authorList": "A et al",
  "publicationDate": "17th July 1991",
  "abstract": "Lorem ipsum dolor sit amet, consectetur adipiscing elit.  "
},
{
  "title": "Another title",
  "authorList": "B et al",
  "publicationDate": "8th December 2020",
  "abstract": "Lorem ipsum dolor sit amet, consectetur adipiscing elit.  "
}
]

function SearchField() {

  return (
    <>
    <input id="searchBox" type="text" />
    <button>Search</button>
    </>
  )
}

function PaperSummaries( { papers } ) {

  if (papers.length === 0) return <></>

  return papers.map(paper => {
    return (<>
    <PaperSummary paper={paper} />
    <br></br>
    </>)
  })
}

function PaperSummary({ paper }) {
  return (
    <>
    <h2>{paper.title}</h2>
    <h3><i>{paper.publicationDate}</i> - {paper.authorList}</h3>
    <p>{paper.abstract}</p>
    </>
  )
}

export default function MyApp() {
  return (
    <div>
      <h1>Preprint Sanity</h1>
      <SearchField />
      <PaperSummaries papers={PAPERS} />
    </div>
  );
}

```

I have no particular talent in terms of design, and I'm not too worried about the looks of the site for now, so the simple, circa Web 1.0 look will do fine for now. At some point I will probably find a good template to work with so that the app becomes responsive etc. But for now, it's time to start putting the dynamics into the site.

Reading further into the React tutorials, I need to think about the statefulness of the page. As I see it, the two stateful parts are what is typed into the search box, and the list of papers displayed on the page. The logic will then go something along the lines of;

1. The user enters a search term into the search box
2. The frontend sends this search term to the backend
3. The backend embeds the search term, finds the most similar papers, and sends these back to the frontend
4. The frontend displays the matched papers

Before building the backend properly, I decided to make a dummy route to continue building and testing the frontend. The route simply returns a couple of random papers from a list of 4 dummy papers;

```python
@app.route('/random_dummy_paper')
def random_dummy_paper():

    papers = [
        {
            "title": "A title",
            "authorList": "A et al",
            "publicationDate": "17th July 1991",
            "abstract": "Lorem ipsum dolor sit amet, consectetur adipiscing elit.  "
        },
        {
            "title": "Another title",
            "authorList": "B et al",
            "publicationDate": "8th December 2020",
            "abstract": "Lorem ipsum dolor sit amet, consectetur adipiscing elit.  "
        },
        {
            "title": "Yet another title",
            "authorList": "c et al",
            "publicationDate": "3rd February 2016",
            "abstract": "Lorem ipsum dolor sit amet, consectetur adipiscing elit.  "
        },
        {
            "title": "Such title, much paper",
            "authorList": "D et al",
            "publicationDate": "15th October 1955",
            "abstract": "Lorem ipsum dolor sit amet, consectetur adipiscing elit.  "
        }
    ]

    return list(np.random.choice(papers, size=2))
```

It took me a little while to get my head around handling state properly, and figuring out which component should be responsible for what. I managed to get it working by adding a top level state variable to the app, representing the papers currently in the PaperSummaries component. I then pass the setter for this component to the search bar. The search bar then sends the request to the backend and uses the setter to update the visible papers. The changed components look like so;

```javascript

function SearchField({ setPapersInView }) {

  const fetchPapersForSearchTerm = async () => {
    let searchBox = document.getElementById("searchBox");
    let searchTerm = searchBox.value;

    fetch("/random_dummy_paper")
    .then( (resp) => {
      console.log(resp)
      return resp.json()
    })
    .then((papers) => {
      setPapersInView(papers)
    })

  }

  return (
    <>
    <input id="searchBox" type="text" />
    <button onClick={fetchPapersForSearchTerm} >Search</button>
    </>
  )
}

export default function MyApp() {

  const [papersInView, setPapersInView] = useState([]);

  return (
    <div>
      <h1>Preprint Sanity</h1>
      <SearchField setPapersInView={setPapersInView} />
      <PaperSummaries papers={papersInView} />
    </div>
  );
}
```

It feels a little bit weird to me how the responsibility for updating the state of the papers component is so far away from that component, but perhaps this is how it's supposed to be with React. I'll see how it feels as I get more used to the framework.

The next step is to actually add the functionality to the backend, i.e., embedding the search term, finding the most similar papers and then returning their details. I realised pretty quickly that I currently don't store a bunch of the information that I want to display on the page (such as the actual text of the abstract, the paper title, publication date, authors etc). I have two options; download, store and then serve this information myself, or hook into the arxiv API to fetch it. I'm thinking that at least in the short term, hooking into the arxiv API is going to be the simplest solution (and might even be the best choice in the long term).

Querying the arxiv api turned out to be very straightforward (I don't know why I struggled so much with it earlier). I wrote a few simple functions to facilitate what I need to do for now. I expect I might need to add a bit more sophistication in the future, so I left some space for that.

```python
from dataclasses import dataclass
from typing import List, Dict, Any
from urllib.parse import urlencode
import feedparser
from html2text import html2text

@dataclass
class ArxivPaper:

    title: str
    authors: List[str]
    publish_date: str
    abstract: str

    def to_dict(self) -> Dict[str, Any]:

        return {
            "title": self.title,
            "authorList": ", ".join(self.authors),
            "publicationDate": self.publish_date,
            "abstract": self.abstract
        }


ARXIV_API_URL = "http://export.arxiv.org/api/query"

def get_formatted_arxiv_api_url(
        search_query: str = None,
        id_list: List[str] = None,
        start: int = None,
        max_results: int = None
):
    query_params = {}
    if search_query is not None:
        query_params['search_query'] = search_query
    if id_list is not None:
        query_params['id_list'] = ','.join(map(str,id_list))
    if start is not None:
        query_params['start'] = start
    if max_results is not None:
        query_params['max_results'] = max_results
            
    return f"{ARXIV_API_URL}?{urlencode(query_params)}"

def fetch_arxiv_papers(id_list: List[str]) -> List[ArxivPaper]:

    url = get_formatted_arxiv_api_url(id_list=id_list)

    paper_details = feedparser.parse(url)['entries']

    arxiv_papers = [
        ArxivPaper(
        title=paper['title'],
        abstract=html2text(paper['summary']),
        publish_date=paper['published'],
        authors=[author['name'] for author in paper['authors']]
        )
        for paper in paper_details
    ]

    return arxiv_papers
```

Then I could replace my dummy papers route to actually have the functionality I need from my earlier work embedding papers;

```python
@app.route('/get_closest_papers', methods=['POST'])
def get_closest_papers():

    if not request.method == "POST":
        return ""

    request_data = request.get_json()

    search_term = request_data['search_term']

    embedding = embed_abstract(search_term).squeeze()
    paper_ids = get_closest_papers_to_embedding(embedding)

    arxiv_papers = fetch_arxiv_papers(paper_ids)

    return [paper.to_dict() for paper in arxiv_papers]
```

and update the frontend component to make the proper POST request

```javascript
function SearchField({ setPapersInView }) {

  const fetchPapersForSearchTerm = async () => {
    let searchBox = document.getElementById("searchBox");
    let searchTerm = searchBox.value;

    let postBody = {
      "search_term": searchTerm
    }

    fetch(
      "/get_closest_papers",
      {
        method: "POST",
        headers: {'Content-Type': 'application/json'}, 
        body: JSON.stringify(postBody)
      }
    )
    .then( (resp) => {
      return resp.json()
    })
    .then((papers) => {
      setPapersInView(papers)
    })

  }

  return (
    <>
    <input id="searchBox" type="text" />
    <button onClick={fetchPapersForSearchTerm} >Search</button>
    </>
  )
}
```
and everything works, or at least functionally. It's not the prettiest, and isn't reactive at all, but those are problems for the future. 

In the next post, I want to add some more features. Top of my list is a "show me similar papers" feature, but I may also start working on the paper favouriting feature. I also want to do a bit of repo maintenance, setting up stylecheckers and linters, and writing docstrings, before that job becomes unmanageable.
