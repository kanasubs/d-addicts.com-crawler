d-addicts.com-crawler
=======
[![FOSSA Status](https://app.fossa.io/api/projects/git%2Bhttps%3A%2F%2Fgithub.com%2Fkanasubs%2Fd-addicts.com-crawler.svg?type=small)](https://app.fossa.io/projects/git%2Bhttps%3A%2F%2Fgithub.com%2Fkanasubs%2Fd-addicts.com-crawler?ref=badge_small)
[![Build Status](https://travis-ci.org/kanasubs/d-addicts.com-crawler.svg?branch=master)](https://travis-ci.org/kanasubs/d-addicts.com-crawler)

A Python web spider library and CLI program to crawl for subtitles links in [d-addicts.com](https://www.d-addicts.com/).

### Install packages
-------
```
pip3 install beautifulsoup4 reppy html5lib
```

### Usage
-------
#### As a library
```python
from daddicts_spider import DAddictsSpider

all_sub_links = set()
delay_between_requests = 6 # optional arg to DAddictsSpider
for sub_links in DAddictsSpider(delay_between_requests):
  print(sub_links)
  all_sub_links |= sub_links
```
This function can run for quite a bit, so feel free to interrupt the loop and use the links stored in `all_sub_links` so far.

#### As a CLI program
```
./daddicts_spider.py <opt_delay_in_secs>
```


### Testing
-------
`pip3 install nosetests` and then run `nosetests` in the project root directory.
