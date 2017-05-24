#!/usr/bin/env python3

from itertools import groupby
from bs4 import BeautifulSoup  # TODO needs setup pip3 install beautifulsoup4
import urllib.request
from urllib.parse import urljoin
from reppy.robots import Robots
from reppy.exceptions import ReppyException
from time import sleep
from abc import ABC, abstractmethod

def unsorted_group_by(coll, fn):
    sorted_coll = sorted(coll, key=fn)
    group_pairs = groupby(sorted_coll, fn)
    groups = {}
    for k,v in group_pairs:
        groups[k] = list(v)
    return groups

file_types_of_interest = ["ass", "srt"]

class PageStore:
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

class FileLinkStore:
    def __init__(self):
        self.visited_links_of_interesting_files = set()

    def update(self, links_to_files_of_interest):
        links_to_files_of_interest -= self.visited_links_of_interesting_files
        self.visited_links_of_interesting_files |= links_to_files_of_interest
        return links_to_files_of_interest

class AbstractSpider(ABC):
    default_delay = 61

    def __iter__(self): return self

    @abstractmethod
    def __next__(self): pass

    @staticmethod
    def download(link):
        return urllib.request.urlopen(link).read()

    @staticmethod
    def tag_file_or_page_link(link):
        if 'file.php?id=' in link: return 'subs'
        else:                      return 'pages'

    @classmethod
    def group_links(cls, links):
        grouped_links = unsorted_group_by(links, cls.tag_file_or_page_link)
        grouped_links['subs'] = set(grouped_links.get('subs') or set())
        grouped_links['pages'] = set(grouped_links.get('pages') or set())
        return grouped_links

    @staticmethod
    def filter_useful_links(links):
        """PASSTHROUGH STUB"""
        return links

    @classmethod
    def get_delay(cls, url):
        robots_url = urljoin(url, 'robots.txt')
        try:
            robots = Robots.fetch(robots_url)
            delay = robots.agent('None').delay
        except ReppyException:
            delay = cls.default_delay
        return delay

class Spider:
    def __init__(self, links):
        self.page_store = PageStore(links)
        self.file_link_store = FileLinkStore()

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

class DAddictsSpider(AbstractSpider):
    def __init__(self, delay=None):
        if delay is None: self.get_delay('http://www.d-addicts.com')
        self.crawl = self.with_crawl_fn(self.extract_topic_links)
        self.topic_links = self.crawl("http://www.d-addicts.com/forums/page/subtitles#Japanese")
        self.crawl = self.with_crawl_fn(self.extract_links_of_interest)
        self.file_link_store = FileLinkStore()
        self.delay = delay

    @staticmethod
    def extract_links_of_interest(html_page):
        return extract_topic_links(html_page)

    @staticmethod
    def extract_topic_links(html_page):
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

    @classmethod
    def with_crawl_fn(cls, crawl_fn):
        def crawl_(link):
            html_page = cls.download(link)
            links = crawl_fn(html_page)
            return cls.filter_useful_links(links)
        return crawl_

    def __next__(self):
        sleep(self.delay)
        links_to_files_of_interest = set()
        if self.topic_links:
            try:
                links = self.crawl(self.topic_links.pop())
                link_groups = group_links(links)
                links_to_files_of_interest = self.file_link_store.update(link_groups['subs'])
            except Exception: pass
            return links_to_files_of_interest
        else: raise StopIteration()

#for file_links in Spider(): print(file_links)
