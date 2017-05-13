#!/usr/bin/env python3

from itertools import groupby
from bs4 import BeautifulSoup  # TODO needs setup pip3 install beautifulsoup4
import urllib.request
from urllib.parse import urljoin
from reppy.robots import Robots
from reppy.exceptions import ReppyException
from time import sleep

def unsorted_group_by(coll, fn):
    sorted_coll = sorted(coll, key=fn)
    group_pairs = groupby(sorted_coll, fn)
    groups = {}
    for k,v in group_pairs:
        groups[k] = list(v)
    return groups

file_types_of_interest = ["ass", "srt"]

def tag_file_or_page_link(link):
    if 'file.php?id=' in link: return 'subs'
    else:                      return 'pages'

def group_links(links):
    grouped_links = unsorted_group_by(links, tag_file_or_page_link)
    grouped_links['subs'] = set(grouped_links.get('subs') or set())
    grouped_links['pages'] = set(grouped_links.get('pages') or set())
    return grouped_links

def download(link):
    return urllib.request.urlopen(link).read()

def d_addicts_extract_http_links(html_page):
    soup = BeautifulSoup(html_page, "html5lib") # TODO add html5lib to setup
    links = set()
    jp_subs_heading = soup.find('h3', text='Japanese Subtitles')
    next_sibling = jp_subs_heading.next_sibling
    while next_sibling:
        jp_subs_link = next_sibling.find('a')
        if jp_subs_link and jp_subs_link != -1: # TODO search why find returns -1
            jp_subs_href = jp_subs_link.get('href')
            links.add(jp_subs_href)
        next_sibling = next_sibling.next_sibling
    return links

def filter_useful_links(links):
    """PASSTHROUGH STUB"""
    return links

def crawl(link):
    return filter_useful_links(d_addicts_extract_http_links(download(link)))

class PageStore():
    def __init__(self, next_pages_to_crawl):
        self.next_pages_to_crawl = next_pages_to_crawl
        self.crawled_links = set()

    def has(self): return bool(self.next_pages_to_crawl)

    def pop(self):
        new_page_to_crawl = self.next_pages_to_crawl.pop()
        self.crawled_links.add(new_page_to_crawl)
        return new_page_to_crawl

    def update(self, pages_to_crawl):
        pages_to_crawl -= self.crawled_links
        self.next_pages_to_crawl |= pages_to_crawl

class FileLinkStore():
    def __init__(self):
        self.visited_links_of_interesting_files = set()

    def update(self, links_to_files_of_interest):
        links_to_files_of_interest -= self.visited_links_of_interesting_files
        self.visited_links_of_interesting_files |= links_to_files_of_interest
        return links_to_files_of_interest

d_addicts_crawler_default_delay = 61

def get_delay(url):
    robots_url = urljoin(url, 'robots.txt')
    try:
        robots = Robots.fetch(robots_url)
        delay = robots.agent('None').delay
    except ReppyException:
        delay = d_addicts_crawler_default_delay
    return delay

class Spider:
    def __init__(self, links):
        self.page_store = PageStore(links)
        self.file_link_store = FileLinkStore()

    def __iter__(self): return self

    def __next__(self):
        links_to_files_of_interest = set()
        if self.page_store.has():
            try:
                links = crawl(self.page_store.pop())
                link_groups = group_links(links)
                self.page_store.update(link_groups['pages'])
                links_to_files_of_interest = self.file_link_store.update(link_groups['subs'])
            except Exception: pass
            return links_to_files_of_interest
        else: raise StopIteration()

class DAddictsSpider:
    def __init__(self, delay=get_delay('http://www.d-addicts.com')):
        self.topic_links = crawl("http://www.d-addicts.com/forums/page/subtitles#Japanese")
        self.file_link_store = FileLinkStore()
        self.delay = delay

    def __iter__(self): return self

    def __next__(self):
        sleep(self.delay)
        links_to_files_of_interest = set()
        if self.topic_links:
            try:
                links = crawl(self.topic_links.pop())
                link_groups = group_links(links)
                links_to_files_of_interest = self.file_link_store.update(link_groups['subs'])
            except Exception: pass
            return links_to_files_of_interest
        else: raise StopIteration()

#for file_links in Spider(): print(file_links)
