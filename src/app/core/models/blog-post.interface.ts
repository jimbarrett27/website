export interface BlogPostSummary {
  slug: string;
  title: string;
  description: string;
  pubDate: string | null;
  updatedDate: string | null;
  heroImage: string | null;
}

export interface BlogPost extends BlogPostSummary {
  content: string;
}
