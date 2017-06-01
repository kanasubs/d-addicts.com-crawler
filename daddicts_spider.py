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


FILE_TYPES_OF_INTEREST = ["ass", "srt"]


def unsorted_group_by(coll, fun):
    sorted_coll = sorted(coll, key=fun)
    group_pairs = groupby(sorted_coll, fun)
    groups = {}
    for k, val in group_pairs:
        groups[k] = list(val)
    return groups


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
    def __init__(self, take=None):
        self.visited_links = set()
        self.take = take

    def update(self, links_to_files_of_interest):
        links_to_files_of_interest -= self.visited_links
        self.visited_links |= links_to_files_of_interest
        res = links_to_files_of_interest
        return res

    def can_take(self):
        if self.take:
            return len(self.visited_links) < self.take
        else:
            return True


class AbstractSpider(ABC):
    default_delay = 61

    def __iter__(self):
        return self

    @abstractmethod
    def __next__(self):
        self.take += 1

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

    @staticmethod
    def get_robots_delay(url):
        robots_url = urllib.parse.urljoin(url, 'robots.txt')
        try:
            robots = Robots.fetch(robots_url)
            delay = robots.agent('None').delay
        except ReppyException:
            delay = None

        return delay

    @classmethod
    def choose_delay(cls, user_delay, url):
        if user_delay is not None:
            delay = user_delay
        else:
            robots_delay = cls.get_robots_delay(url)
            if robots_delay is not None:
                delay = robots_delay
            else:
                delay = cls.default_delay

        return delay


class DAddictsSpider(AbstractSpider):
    base_url = "http://www.d-addicts.com/forums/page/subtitles#Japanese"
    file_of_interest_subs = 'file.php?id='
    file_of_interest_pattern = re.compile(re.escape(file_of_interest_subs))

    def __init__(self, delay=None, take=None):
        self.delay = self.choose_delay(delay, 'http://www.d-addicts.com')
        self.crawl = self.with_crawl_fn(self.extract_topic_links)
        self.topic_links = self.crawl(self.base_url)
        self.crawl = self.with_crawl_fn(self.extract_links_of_interest)
        self.file_link_store = FileLinkStore(take)

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

        if self.topic_links and self.file_link_store.can_take():
            try:
                links = self.crawl(self.topic_links.pop())
                links_to_files_of_interest = self.file_link_store.update(links)
            except urllib.error.URLError:
                pass
        else:
            raise StopIteration()

        return links_to_files_of_interest


class MainSpider(DAddictsSpider):
    def __init__(self, cmd_line_args):
        super().__init__(self.maybe_get_delay(cmd_line_args),
                         self.maybe_take_some(cmd_line_args))

    @staticmethod
    def maybe_get_delay(cmd_line_args):
        if len(cmd_line_args) > 1:
            return int(cmd_line_args[1])

    @staticmethod
    def maybe_take_some(cmd_line_args):
        if len(cmd_line_args) > 2:
            return int(cmd_line_args[2])


def main(cmd_line_args):
    for sub_links in MainSpider(cmd_line_args):
        for sub_link in sub_links:
            print(sub_link)


if __name__ == '__main__':
    main(sys.argv)
