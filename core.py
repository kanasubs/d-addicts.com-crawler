#!/usr/bin/env python3

from itertools import groupby
import urllib.request

def unsorted_group_by(coll, fn):
    sorted_coll = sorted(coll, key=fn)
    group_pairs = groupby(sorted_coll, fn)
    groups = {}
    for k,v in group_pairs:
        groups[k] = list(v)
    return groups

file_types_of_interest = ["ass", "srt"]

def tag_file_or_page_link(link):
    if 'file.php?id=' in link:
        return 'subs'
    else:
        return 'pages'

def group_links(links):
    grouped_links = unsorted_group_by(links, tag_file_or_page_link)
    grouped_links['subs'] = set(grouped_links.get('subs') or set())
    grouped_links['pages'] = set(grouped_links.get('pages') or set())
    return grouped_links

def extract_http_links(page_content):
    """STUB"""
    return {"http://www.d-addicts.com/forums/download/file.php?id=51630",
            "http://www.d-addicts.com/forums/some_topic"}

def download(link):
    return urllib.request.urlopen(link).read()

def filter_useful_links(links):
    """PASSTHROUGH STUB"""
    return links

def crawl(link):
    return filter_useful_links(extract_http_links(download(link)))

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
            except Exception:
                pass
            return links_to_files_of_interest
        else: raise StopIteration()

class DAddictsSpider:
    def __init__(self):
        self.topic_links = crawl("http://www.d-addicts.com/forums/page/subtitles#Japanese")
        self.file_link_store = FileLinkStore()

    def __iter__(self): return self

    def __next__(self):
        links_to_files_of_interest = set()
        if self.topic_links:
            try:
                links = crawl(self.topic_links.pop())
                link_groups = group_links(links)
                links_to_files_of_interest = self.file_link_store.update(link_groups['subs'])
            except Exception:
                pass
            return links_to_files_of_interest
        else: raise StopIteration()

#for file_links in Spider(): print(file_links)
