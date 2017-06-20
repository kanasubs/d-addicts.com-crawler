#!/usr/bin/env python3

import argparse
import sys
import re
import urllib
import ast
import pathlib

from itertools import groupby, islice
from time import sleep
from abc import ABC, abstractmethod, abstractclassmethod
from furl import furl

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


class Path(object):
    def __init__(self, file_path):
        path = pathlib.Path(file_path)
        self.read_text = path.read_text
        self.write_text = path.write_text
        self.is_file = path.is_file
        self.touch = path.touch
        self.stat = path.stat
        self.unlink = path.unlink

    def is_file_with_content(self):
        return self.is_file() and self.stat().st_size > 0


class Set(object):
    def __init__(self, init_set): self.set_ = init_set

    def pop(self): return self.set_.pop()

    def __next__(self): return self.pop()

    def __iter__(self): return self

    def __len__(self): return len(self.set_)

    def __repr__(self):
        return repr(self.set_) if self.set_ else ""


class FilePersistableSet(Set, Path):
    def __init__(self, file_path, init_set):
        Path.__init__(self, file_path)
        Set.__init__(self, self.retrieve() or init_set)

    def persist(self):
        self.write_text(repr(self))

    def retrieve(self):
        if self.is_file_with_content():
            return ast.literal_eval(self.read_text())
        return set()


class FileLinkStore(object):
    def __init__(self, take=None):
        self.visited_links = set()
        self.take = take

    def update(self, links_to_files_of_interest):
        links_to_files_of_interest -= self.visited_links
        self.visited_links |= links_to_files_of_interest
        return links_to_files_of_interest

    def can_take(self):
        return (self.take is None) or len(self.visited_links) < self.take


class ABCSpider(ABC):
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
            rel_links = crawl_fn(html_page)
            links = set(map(cls.complete_link, rel_links))
            return links
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


class DAddictsSpider(ABCSpider):
    base_url = "http://www.d-addicts.com/forums/page/subtitles#Japanese"
    file_of_interest_subs = 'file.php?id='
    file_of_interest_pattern = re.compile(re.escape(file_of_interest_subs))

    def __init__(self, delay=None, take=None):
        delay_either = self.choose_delay(delay, 'http://www.d-addicts.com')
        self.delay = delay_either.getValue()
        self.crawl = self.with_crawl_fn(self.extract_topic_links)
        topic_links = self.crawl(self.base_url)
        self.topic_links = iter(FilePersistableSet('daddicts_page_links.txt', topic_links))
        self.crawl = self.with_crawl_fn(self.extract_links_of_interest)
        self.file_link_store = FileLinkStore(take)

    @staticmethod
    def complete_link(rel_link):
        original_link = furl('http://www.d-addicts.com/forums/').join(rel_link)
        return original_link.remove(['sid']).url

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
            if jp_subs_link and jp_subs_link != -1:
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
            except StopIteration:
                self.topic_links.persist()
                raise StopIteration()
        else:
            self.topic_links.persist()
            raise StopIteration()

        # Continuously persisting to avoid not saving with 'for' exit
        # triggered by islice instead of iter __next__ with StopIteration.
        # Might be better anyway as continuously persisting will support
        # user interruption and then resuming from that point.
        self.topic_links.persist()

        return links_to_files_of_interest


class AppArgParser(argparse.ArgumentParser):
    def __init__(self):
        take_description = "take at least and around 'n' links. " + \
                           "Will resume from last point when calling the program again."
        crawl_description = "Crawl 'n' times. " + \
                            "Will resume from last point when calling the program again."
        HelpFormatter = argparse.HelpFormatter
        formatter_class_factory = lambda prog: HelpFormatter(prog, max_help_position=27)
        super().__init__(prog='daddicts_spider.py', formatter_class=formatter_class_factory)
        self.add_argument('-d', '--delay', type=int, help="delay in seconds between HTTP requests")
        group = self.add_mutually_exclusive_group()
        group.add_argument('-t', '--take', type=int, help=take_description)
        group.add_argument('-c', '--crawl', type=int, help=crawl_description)


def main(cli_args):
    delay, take, crawl = cli_args.delay, cli_args.take, cli_args.crawl
    delay, take, crawl = delay and int(delay), take and int(take), crawl and int(crawl)
    crawl_times = crawl or sys.maxsize
    for sub_links in islice(DAddictsSpider(delay, take), crawl_times):
        for sub_link in sub_links:
            print(sub_link)


if (__name__ == '__main__') and not sys.flags.interactive:
    cli_args = AppArgParser().parse_args()
    main(cli_args)
