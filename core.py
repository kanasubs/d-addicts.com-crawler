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

def extract_http_links(page_content):
    """STUB"""
    return {"http://www.d-addicts.com/forums/download/file.php?id=51630",
            "http://www.d-addicts.com/forums/some_topic"}

def crawl(page): return extract_http_links(download_file(page))

def Crawler(crawled_pages=set(),
            next_pages_to_crawl={"http://www.d-addicts.com/forums/page/subtitles#Japanese"}):
    if next_pages_to_crawl:
        next_page_to_crawl = next_pages_to_crawl.pop()
        links = crawl(next_page_to_crawl) # TODO try this
        (links_to_files_of_interest, pages_to_crawl) = separate_files_from_pages(links)
        pages_to_crawl -= crawled_pages
        crawled_pages.add(next_page_to_crawl)
        next_pages_to_crawl.union(pages_to_crawl)
        yield links_to_files_of_interest

for file_links in Crawler(): print(file_links)
