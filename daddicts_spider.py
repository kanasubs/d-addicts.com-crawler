#!/usr/bin/env python3

import re
import sys
import urllib

from itertools import groupby
from time import sleep
from abc import ABC, abstractmethod, abstractclassmethod

from bs4 import BeautifulSoup
from reppy.robots import Robots
from reppy.exceptions import ReppyException


def unsorted_group_by(coll, fun):
    sorted_coll = sorted(coll, key=fun)
    group_pairs = groupby(sorted_coll, fun)
    groups = {}
    for k, val in group_pairs:
        groups[k] = list(val)
    return groups

FILE_TYPES_OF_INTEREST = ["ass", "srt"]


class PageStore:
    def __init__(self, next_pages_to_crawl):
        self.next_pages_to_crawl = next_pages_to_crawl
        self.crawled_links = set()

    def has(self):
        return bool(self.next_pages_to_crawl)

    def pop(self):
        new_page_to_crawl = self.next_pages_to_crawl.pop()
        self.crawled_links.add(new_page_to_crawl)
        return new_page_to_crawl

    def update(self, pages_to_crawl):
        pages_to_crawl -= self.crawled_links
        self.next_pages_to_crawl |= pages_to_crawl


class FileLinkStore:
    def __init__(self):
        self.visited_links = set()

    def update(self, links_to_files_of_interest):
        links_to_files_of_interest -= self.visited_links
        self.visited_links |= links_to_files_of_interest
        return links_to_files_of_interest


class AbstractSpider(ABC):
    default_delay = 61

    def __iter__(self):
        return self

    @abstractmethod
    def __next__(self):
        pass

    @staticmethod
    def download(link):
        return urllib.request.urlopen(link).read()

    @classmethod
    def with_crawl_fn(cls, crawl_fn):
        def crawl_(link):
            html_page = cls.download(link)
            links = crawl_fn(html_page)
            return cls.filter_useful_links(links)
        return crawl_

    @abstractclassmethod
    def extract_links_of_interest(cls, html_page):
        pass

    @staticmethod
    def tag_file_or_page_link(link):
        if 'file.php?id=' in link:
            return 'subs'
        return 'pages'

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
        robots_url = urllib.parse.urljoin(url, 'robots.txt')
        try:
            robots = Robots.fetch(robots_url)
            delay = robots.agent('None').delay
        except ReppyException:
            delay = cls.default_delay
        return delay


class Spider(AbstractSpider):
    def __init__(self, links):
        self.page_store = PageStore(links)
        self.file_link_store = FileLinkStore()
        self.crawl = self.with_crawl_fn(self.extract_links_of_interest)

    @classmethod
    def extract_links_of_interest(cls, html_page):
        """PASSTHROUGH STUB"""
        return set()

    def __next__(self):
        links_to_files_of_interest = set()
        if self.page_store.has():
            try:
                links = self.crawl(self.page_store.pop())
                link_groups = self.group_links(links)
                self.page_store.update(link_groups['pages'])
                subs = link_groups['subs']
                links_to_files_of_interest = self.file_link_store.update(subs)
            except urllib.error.URLError:
                pass
            return links_to_files_of_interest
        else:
            raise StopIteration()


class DAddictsSpider(AbstractSpider):
    base_url = "http://www.d-addicts.com/forums/page/subtitles#Japanese"

    def __init__(self, delay=None):
        if delay is None:
            self.delay = self.get_delay('http://www.d-addicts.com')
        else:
            self.delay = delay
        self.crawl = self.with_crawl_fn(self.extract_topic_links)
        self.topic_links = self.crawl(self.base_url)
        self.crawl = self.with_crawl_fn(self.extract_links_of_interest)
        self.file_link_store = FileLinkStore()

    file_of_interest_subs = 'file.php?id='
    file_of_interest_pattern = re.compile(re.escape(file_of_interest_subs))

    @classmethod
    def extract_links_of_interest(cls, html_page):
        soup = BeautifulSoup(html_page, "html5lib")
        links = set()
        for link in soup.find_all('a', href=cls.file_of_interest_pattern):
            links.add(link['href'])
        return links

    @staticmethod
    def extract_topic_links(html_page):
        soup = BeautifulSoup(html_page, "html5lib")
        links = set()
        jp_subs_heading = soup.find('h3', text='Japanese Subtitles')
        next_sibling = jp_subs_heading.next_sibling
        while next_sibling:
            jp_subs_link = next_sibling.find('a')
            if jp_subs_link and jp_subs_link != -1:  # TODO find why ret=-1 ?
                jp_subs_href = jp_subs_link.get('href')
                links.add(jp_subs_href)
            next_sibling = next_sibling.next_sibling
        return links

    def __next__(self):
        sleep(self.delay)
        links_to_files_of_interest = set()
        if self.topic_links:
            try:
                links = self.crawl(self.topic_links.pop())
                links_to_files_of_interest = self.file_link_store.update(links)
            except urllib.error.URLError:
                pass
            return links_to_files_of_interest
        else:
            raise StopIteration()


def maybe_override_delay(cmd_line_args):
    if len(cmd_line_args) > 1:
        return int(sys.argv[1])

if __name__ == '__main__':
    DELAY = maybe_override_delay(sys.argv)
    if DELAY:
        DADDICTS_SPIDER = DAddictsSpider(DELAY)
    else:
        DADDICTS_SPIDER = DAddictsSpider()
    for sub_links in DADDICTS_SPIDER:
        for sub_link in sub_links:
            print(sub_link)
