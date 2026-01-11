export interface Publication {
  title: string;
  authors: string;
  url: string;
}

export interface PublicationsData {
  firstAuthor: Publication[];
  other: Publication[];
  mastersTheses: Publication[];
  patents: Publication[];
}
