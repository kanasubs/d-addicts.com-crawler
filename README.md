  # d-addicts.com-crawler
A Python web spider library to crawl for subtitles links in [d-addicts.com](https://www.d-addicts.com/).

## Install packages
```
pip3 install beautifulsoup4 reppy html5lib
```

## Usage example
```python
from core import DAddictsSpider

all_sub_links = set()
delay_between_requests = 2 # optional to DAddictsSpider
for sub_links in DAddictsSpider(delay_between_requests):
  print(sub_links)
  all_sub_links |= sub_links
```
This function can run for quite a bit, so feel free to interrupt the loop and use the links stored in `all_sub_links` so far.

## Testing
`pip3 install nosetests` and then run `nosetests` in the project root directory.
