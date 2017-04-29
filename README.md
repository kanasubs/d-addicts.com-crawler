# d-addicts.com-crawler
Crawls for subtitles links in d-addicts.com

## Input
Optionally accepts a list of relative links to `d-addicts.com` for crawling.
In case no list is provided, uses `http://www.d-addicts.com/forums/page/subtitles#Japanese` instead.

## Output
A tuple of `(link, next_crawl_list, file_digest)`. `file_digest` is last because it may be an optional return
value for clients not interested in obtaining it. Use digest algorithm at your discretion.

## Testing
1. TODO 
