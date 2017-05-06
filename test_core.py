#!/usr/bin/env python3

import unittest
from core import *

class TopLevelTest(unittest.TestCase):

    def test_tag_file_or_page_link(self):
        self.assertEqual(tag_file_or_page_link('d.com/file.php?id='), 'subs')
        self.assertEqual(tag_file_or_page_link('d.com/page1'), 'pages')

    def test_unsorted_group_by(self):
        links = {"d.com/1file.php?id=", "d.com/page1", "d.com/page2"}
        self.assertDictEqual(unsorted_group_by(links, tag_file_or_page_link),
                             {'subs': ["d.com/1file.php?id="],
                              'pages': ["d.com/page1", "d.com/page2"]})

    def test_group_links(self):
        self.assertSetEqual(group_links({"d.co/p1"}).get('subs'), set())
        self.assertSetEqual(group_links({"d.co/file.php?id="}).get('pages'), set())
        self.assertSetEqual(group_links({"d.co/p1"}).get('pages'), {"d.co/p1"})

class PageStoreTest(unittest.TestCase):
    def test_page_store(self):
        default_page_store = PageStore()
        assert default_page_store.has()
        assert default_page_store.pop()
        self.assertFalse(default_page_store.has())
        default_page_store = PageStore()
        assert default_page_store.has()
        page_store = PageStore({"d.co/p1"})
        self.assertEqual(page_store.pop(), "d.co/p1")
        self.assertFalse(page_store.has())
        page_store.update({"d.co/p2"})
        self.assertEqual(page_store.pop(), "d.co/p2")

class FileLinkStoreTest(unittest.TestCase):
    def test_file_link_store(self):
        file_link_store = FileLinkStore()
        links = file_link_store.update({'d.co/file.php?id=1'})
        self.assertSetEqual(links, {'d.co/file.php?id=1'})
        links = file_link_store.update({'d.co/file.php?id=1', 'd.co/file.php?id=2'})
        self.assertSetEqual(links, {'d.co/file.php?id=2'})

if __name__ == '__main__':
    with unittest.main() as main: pass
