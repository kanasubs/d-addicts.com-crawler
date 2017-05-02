# d-addicts.com-crawler
A Python library to crawl for subtitles links in [d-addicts.com](https://www.d-addicts.com/).

## Input
Optionally accepts a tuple of relative page links to [d-addicts.com](https://www.d-addicts.com/) that were crawled or are to be crawled - `(crawled_pages_list, next_pages_to_crawl_list)`.
In case no tuple is provided, uses [http://www.d-addicts.com/forums/page/subtitles#Japanese](http://www.d-addicts.com/forums/page/subtitles#Japanese) instead.

## Output
```python
links_from_first_page_found_to_have_links = [(link1, file_digest1), (link2, file_digest2) ..]
crawled_pages_list = [(link1, page_digest1, changed_at), (link2, page_digest2, changed_at) ..]
return (links_from_first_page_found_to_have_links, (crawled_pages_list, next_pages_to_crawl_list))
```
`file_digest` is last because it may be an optional return
value for clients not interested in obtaining it. Use digest algorithm at your discretion.

## Testing
1. TODO 
