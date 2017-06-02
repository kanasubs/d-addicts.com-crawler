d-addicts.com-crawler
=======
[![FOSSA Status](https://app.fossa.io/api/projects/git%2Bhttps%3A%2F%2Fgithub.com%2Fkanasubs%2Fd-addicts.com-crawler.svg?type=small)](https://app.fossa.io/projects/git%2Bhttps%3A%2F%2Fgithub.com%2Fkanasubs%2Fd-addicts.com-crawler?ref=badge_small)
[![Build Status](https://travis-ci.org/kanasubs/d-addicts.com-crawler.svg?branch=master)](https://travis-ci.org/kanasubs/d-addicts.com-crawler)
[![Coverage Status](https://coveralls.io/repos/github/kanasubs/d-addicts.com-crawler/badge.svg?branch=master)](https://coveralls.io/github/kanasubs/d-addicts.com-crawler?branch=master)
[![Code Climate](https://codeclimate.com/github/kanasubs/d-addicts.com-crawler/badges/gpa.svg)](https://codeclimate.com/github/kanasubs/d-addicts.com-crawler)
[![Issue Count](https://codeclimate.com/github/kanasubs/d-addicts.com-crawler/badges/issue_count.svg)](https://codeclimate.com/github/kanasubs/d-addicts.com-crawler)

A Python web spider library and CLI program to crawl for subtitles links in [d-addicts.com](https://www.d-addicts.com/).

### Install dependencies
-------
```
pip3 install html5lib -r requirements.txt
```

### Usage
-------
#### As a library
```python
from daddicts_spider import DAddictsSpider

all_sub_links = set()
delay_between_requests = 6  # optional arg to DAddictsSpider
take_around_n_links = 10    # optional arg to DAddictsSpider
for sub_links in DAddictsSpider(delay_between_requests, take_around_n_links):
    print(sub_links)
    all_sub_links |= sub_links
```

#### As a CLI program
```
./daddicts_spider.py <opt_delay_in_secs> <take_around_n_links>
```

### Testing
-------
`pip3 install nose` and then run `nosetests` in the project's root directory.

### License
-------
Copyright (C) 2017 Carlos C. Fontes.

Licensed under the [MIT License](https://opensource.org/licenses/MIT).
