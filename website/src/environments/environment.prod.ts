/**
 * Production environment (swapped in by angular.json fileReplacements).
 */
export const environment = {
  production: true,
  // Public GCS bucket the telegram_bot tapestry job writes to. Same URL in dev
  // and prod: the objects are public-read and the bucket allows cross-origin GET.
  tapestryBucketBase: 'https://storage.googleapis.com/personal-website-318015-tapestry/tapestry',
  // Public bucket gb_agent/publish.py writes the live run to.
  gbAgentBucketBase: 'https://storage.googleapis.com/personal-website-318015-gb-agent',
};
