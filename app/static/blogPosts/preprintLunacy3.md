This post relates to my preprint lunacy project. You can find the introduction post [here](https://jimbarrett.phd/blog/6). This post covers my progress up to commit **TODO**.

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

// const PAPERS = []

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