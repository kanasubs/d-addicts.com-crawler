#!/usr/bin/env python

file_types_of_interest = ["ass", "srt"]

def separate_files_from_pages(links):
    """STUB"""
    return ({"http://www.d-addicts.com/forums/download/file.php?id=51630"},
            {"http://www.d-addicts.com/forums/some_topic"})

def download_file(link):
    """STUB"""
    return """dummy_content
           http://www.d-addicts.com/forums/download/file.php?id=51630
           http://www.d-addicts.com/forums/some_topic"""

def get_http_links(page_content):
    """STUB"""
    return {"http://www.d-addicts.com/forums/download/file.php?id=51630",
            "http://www.d-addicts.com/forums/some_topic"}

def crawl(page):
    return get_http_links(download_file(page))

class Crawler(object):
    def __init__(self,
                 crawled_links=set(),
                 next_pages_to_crawl={"http://www.d-addicts.com/forums/page/subtitles#Japanese"}):
        self.crawled_links = crawled_links
        self.next_pages_to_crawl = next_pages_to_crawl

    def __iter__(self):
        return self

    def __next__(self):
        if self.next_pages_to_crawl:
            next_page_to_crawl = self.next_pages_to_crawl.pop()
            links = crawl(next_page_to_crawl)
            (links_to_files_of_interest, pages_to_crawl) = separate_files_from_pages(links)
            # todo pages_to_crawl -= self.crawled_links
            self.crawled_links.add(next_page_to_crawl) # fixme use set op instead
            self.next_pages_to_crawl.union(pages_to_crawl)
            return links_to_files_of_interest
        else:
            raise StopIteration()

for link in Crawler():
    print(link)
