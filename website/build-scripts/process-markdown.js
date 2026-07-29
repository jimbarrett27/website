const fs = require('fs');
const path = require('path');
const matter = require('gray-matter');
const { marked } = require('marked');

const CONTENT_DIR = path.join(__dirname, '..', 'content', 'blog');
const OUTPUT_DIR = path.join(__dirname, '..', 'src', 'assets', 'blog');

// Ensure output directory exists
if (!fs.existsSync(OUTPUT_DIR)) {
  fs.mkdirSync(OUTPUT_DIR, { recursive: true });
}

// Configure marked for GFM
marked.setOptions({
  gfm: true,
  breaks: false
});

// Frontmatter dates are calendar dates ('04 Dec 2017'), which `new Date()` reads as
// local midnight. Calling toISOString() on that shifts the day backwards anywhere east
// of UTC, so the generated JSON depended on the machine doing the build. Reinterpret the
// local year/month/day as UTC midnight to keep output identical everywhere.
function toUtcIsoDate(value) {
  if (!value) return null;
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return null;
  return new Date(Date.UTC(
    parsed.getFullYear(),
    parsed.getMonth(),
    parsed.getDate()
  )).toISOString();
}

// Get all markdown files
const files = fs.readdirSync(CONTENT_DIR).filter(file =>
  file.endsWith('.md') || file.endsWith('.mdx')
);

const blogPosts = [];

files.forEach(file => {
  const filePath = path.join(CONTENT_DIR, file);
  const content = fs.readFileSync(filePath, 'utf-8');

  // Parse frontmatter
  const { data: frontmatter, content: markdownContent } = matter(content);

  // Generate slug from filename (remove extension)
  const slug = file.replace(/\.(md|mdx)$/, '');

  // Convert markdown to HTML
  let htmlContent = marked(markdownContent);

  // Rewrite paths for Angular asset structure
  htmlContent = htmlContent.replace(/src="\/notebooks\//g, 'src="/assets/notebooks/');
  htmlContent = htmlContent.replace(/src="\/static\/images\//g, 'src="/assets/images/');
  htmlContent = htmlContent.replace(/href="\/content\/notebooks\//g, 'href="/assets/notebooks/');

  // Fix HTML-escaped characters in LaTeX math blocks
  // Fix &amp; back to & in align environments
  htmlContent = htmlContent.replace(/\\begin\{align\}[\s\S]*?\\end\{align\}/g, (match) => {
    return match.replace(/&amp;/g, '&');
  });

  // Create blog post object
  const post = {
    slug,
    title: frontmatter.title || 'Untitled',
    description: frontmatter.description || '',
    pubDate: toUtcIsoDate(frontmatter.pubDate),
    updatedDate: toUtcIsoDate(frontmatter.updatedDate),
    heroImage: frontmatter.heroImage || null,
    content: htmlContent
  };

  // Write individual post JSON
  const outputPath = path.join(OUTPUT_DIR, `${slug}.json`);
  fs.writeFileSync(outputPath, JSON.stringify(post, null, 2));
  console.log(`Processed: ${file} -> ${slug}.json`);

  // Add to index (without full content)
  blogPosts.push({
    slug: post.slug,
    title: post.title,
    description: post.description,
    pubDate: post.pubDate,
    updatedDate: post.updatedDate,
    heroImage: post.heroImage
  });
});

// Sort by date (newest first)
blogPosts.sort((a, b) => {
  if (!a.pubDate) return 1;
  if (!b.pubDate) return -1;
  return new Date(b.pubDate).getTime() - new Date(a.pubDate).getTime();
});

// Write index.json
const indexPath = path.join(OUTPUT_DIR, 'index.json');
fs.writeFileSync(indexPath, JSON.stringify(blogPosts, null, 2));
console.log(`\nGenerated index.json with ${blogPosts.length} posts`);
