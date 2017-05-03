#!/usr/bin/env python3

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

def extract_http_links(page_content):
    """STUB"""
    return {"http://www.d-addicts.com/forums/download/file.php?id=51630",
            "http://www.d-addicts.com/forums/some_topic"}

def crawl(page): return extract_http_links(download_file(page))

class PageStore():
    def __init__(self, next_pages_to_crawl={"http://www.d-addicts.com/forums/page/subtitles#Japanese"}):
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

class Crawler:
    def __init__(self):
        self.page_store = PageStore()
        self.file_link_store = FileLinkStore()

    def __iter__(self): return self

    def __next__(self):
        links_to_files_of_interest = set()
        if self.page_store.has():
            try:
                links = crawl(self.page_store.pop())
                (links_to_files_of_interest, pages_to_crawl) = separate_files_from_pages(links)
                self.page_store.update(pages_to_crawl)
            except Exception: pass
            links_to_files_of_interest = self.file_link_store.update(links_to_files_of_interest)
            return links_to_files_of_interest
        else: raise StopIteration()

for file_links in Crawler(): print(file_links)
