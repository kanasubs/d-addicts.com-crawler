#!/usr/bin/env python3

import unittest
from unittest import TestCase
from unittest.mock import patch
from reppy.robots import Robots
from reppy.exceptions import ReppyException
from core import *

class FakeRobots():
    def fetch(self, url): raise(ReppyException())

class TopLevelTest(TestCase):

    def test_unsorted_group_by(self):
        links = {"d.com/1file.php?id=", "d.com/page1", "d.com/page2"}
        self.assertCountEqual(unsorted_group_by(links, AbstractSpider.tag_file_or_page_link),
                              {'subs': ["d.com/1file.php?id="],
                               'pages': ["d.com/page1", "d.com/page2"]})

class PageStoreTest(TestCase):
    def test_page_store(self):
        page_store = PageStore({"d.co/p1"})
        self.assertEqual(page_store.pop(), "d.co/p1")
        self.assertFalse(page_store.has())
        page_store.update({"d.co/p2"})
        self.assertEqual(page_store.pop(), "d.co/p2")

class FileLinkStoreTest(TestCase):
    def test_file_link_store(self):
        file_link_store = FileLinkStore()
        links = file_link_store.update({'d.co/file.php?id=1'})
        self.assertSetEqual(links, {'d.co/file.php?id=1'})
        links = file_link_store.update({'d.co/file.php?id=1', 'd.co/file.php?id=2'})
        self.assertSetEqual(links, {'d.co/file.php?id=2'})

class Spider(unittest.TestCase):
    def test_tag_file_or_page_link(self):
        self.assertEqual(AbstractSpider.tag_file_or_page_link('d.com/file.php?id='), 'subs')
        self.assertEqual(AbstractSpider.tag_file_or_page_link('d.com/page1'), 'pages')

    def test_group_links(self):
        self.assertSetEqual(AbstractSpider.group_links({"d.co/p1"}).get('subs'), set())
        self.assertSetEqual(AbstractSpider.group_links({"d.co/file.php?id="}).get('pages'), set())
        self.assertSetEqual(AbstractSpider.group_links({"d.co/p1"}).get('pages'), {"d.co/p1"})

class DAddictsSpiderTest(unittest.TestCase):
    def test_extract_topic_links(self):
        with open('tests/resources/d_addicts_base_page.html') as f:
            links = DAddictsSpider.extract_topic_links(f.read())
            self.assertGreater(len(links), 543)
            for link in links:
                self.assertIn('www.d-addicts.com/forums/viewtopic.php?t=', link)

    def test_extract_links_of_interest(self):
        with open('tests/resources/viewtopic.php?t=99358') as f:
            links = DAddictsSpider._extract_links_of_interest(f.read())
            self.assertGreater(len(links), 10)
            for link in links:
                self.assertIn(DAddictsSpider._file_of_interest_subs, link)

    def test_get_delay(self): # TODO impl. monad either to properly test right/left branching
        self.assertGreaterEqual(DAddictsSpider.get_delay('http://www.d-addicts.com'), 0)
        with patch('core.Robots', new_callable=FakeRobots):
            self.assertEqual(DAddictsSpider.get_delay('http://www.d-addicts.com'),
                             DAddictsSpider.default_delay)
