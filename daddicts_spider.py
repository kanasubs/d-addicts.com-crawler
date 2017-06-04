#!/usr/bin/env python3

import argparse
import re
import urllib

from itertools import groupby
from time import sleep
from abc import ABC, abstractmethod, abstractclassmethod

from bs4 import BeautifulSoup
from reppy.robots import Robots
from reppy.exceptions import ReppyException

from lib.monad.either import either, Left, Right


def unsorted_group_by(coll, fun):
    sorted_coll = sorted(coll, key=fun)
    group_pairs = groupby(sorted_coll, fun)
    groups = {}
    for k, val in group_pairs:
        groups[k] = list(val)
    return groups


class FileLinkStore(object):
    def __init__(self, take=None):
        self.visited_links = set()
        self.take = take

    def update(self, links_to_files_of_interest):
        links_to_files_of_interest -= self.visited_links
        self.visited_links |= links_to_files_of_interest
        return links_to_files_of_interest

    def can_take(self):
        if self.take is not None:
            return len(self.visited_links) < self.take
        else:
            return True


class AbstractSpider(ABC):
    default_delay = 60

    def __iter__(self): return self

    @abstractmethod
    def __next__(self): self.take += 1

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
    def extract_links_of_interest(cls, html_page): pass

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
            delay = Right(robots.agent('None').delay)
        except ReppyException:
            delay = Left(None)

        return delay

    @classmethod
    def choose_delay(cls, user_delay, url):
        return either(user_delay) \
               .or_call(cls.get_robots_delay, url) \
               .get_or(Left(cls.default_delay))


class DAddictsSpider(AbstractSpider):
    base_url = "http://www.d-addicts.com/forums/page/subtitles#Japanese"
    file_of_interest_subs = 'file.php?id='
    file_of_interest_pattern = re.compile(re.escape(file_of_interest_subs))

    def __init__(self, delay=None, take=None):
        delay_either = self.choose_delay(delay, 'http://www.d-addicts.com')
        self.delay = delay_either.getValue()
        self.crawl = self.with_crawl_fn(self.extract_topic_links)
        self.topic_links = iter(self.crawl(self.base_url))
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

        if self.file_link_store.can_take():
            try:
                links = self.crawl(next(self.topic_links))
                links_to_files_of_interest = self.file_link_store.update(links)
            except urllib.error.URLError:
                pass
        else:
            raise StopIteration()

        return links_to_files_of_interest


def main(cli_args):
    delay, take = int(cli_args.delay), int(cli_args.take)
    for sub_links in DAddictsSpider(delay, take):
        for sub_link in sub_links:
            print(sub_link)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    add_cli_arg = parser.add_argument
    add_cli_arg('-d', '--delay', type=int, help='Delay between HTTP requests')
    add_cli_arg('-t', '--take', type=int, help='Take at least and around n links')
    cli_args = parser.parse_args()
    main(cli_args)
