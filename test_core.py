#!/usr/bin/env python3

import unittest
from core import *

class TestTopLevel(unittest.TestCase):

    def test_tag_file_or_page_link(self):
        self.assertEqual(tag_file_or_page_link('d.com/file.php?id='), 'subs')
        self.assertEqual(tag_file_or_page_link('d.com/page1'), 'pages')

    def test_unsorted_group_by(self):
        links = ["d.com/1file.php?id=", "d.com/page1", "d.com/page2"]
        self.assertEqual(unsorted_group_by(links, tag_file_or_page_link),
                         {'subs': ["d.com/1file.php?id="],
                          'pages': ["d.com/page1", "d.com/page2"]})

    def test_group_links(self):
        self.assertEqual(group_links(["d.co/p1"]).get('subs'), [])
        self.assertEqual(group_links(["d.co/file.php?id="]).get('pages'), [])
        self.assertEqual(group_links(["d.co/p1"]).get('pages'), ["d.co/p1"])

if __name__ == '__main__':
    with unittest.main() as main: pass
