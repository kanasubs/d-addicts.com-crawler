import sys

from unittest import mock, TestCase

from reppy.robots import Robots
from reppy.exceptions import ReppyException

from daddicts_spider import *


class FakeRobots():
    def fetch(self, url):
        raise ReppyException({'obj': self, 'url': url})


class TopLevelTest(TestCase):

    def test_unsorted_group_by(self):
        tag_file_or_page_link = AbstractSpider.tag_file_or_page_link
        links = {"d.com/1file.php?id=", "d.com/page1", "d.com/page2"}
        self.assertCountEqual(unsorted_group_by(links, tag_file_or_page_link),
                              {'subs': ["d.com/1file.php?id="],
                               'pages': ["d.com/page1", "d.com/page2"]})

    def test_maybe_override_delay(self):
        self.assertIsNone(maybe_override_delay(sys.argv))
        sys.argv.append('6')
        self.assertEqual(maybe_override_delay(sys.argv), 6)


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
        links = file_link_store.update({'d.co/file.php?id=1',
                                        'd.co/file.php?id=2'})
        self.assertSetEqual(links, {'d.co/file.php?id=2'})


class AbstractSpiderTest(TestCase):
    def test_tag_file_or_page_link(self):
        tag_file_or_page_link = AbstractSpider.tag_file_or_page_link
        self.assertEqual(tag_file_or_page_link('d.com/file.php?id='), 'subs')
        self.assertEqual(tag_file_or_page_link('d.com/page1'), 'pages')

    def test_group_links(self):
        group_links = AbstractSpider.group_links
        self.assertSetEqual(group_links({"d.co/p1"}).get('subs'), set())
        self.assertSetEqual(group_links({"d.co/file.php?id="}).get('pages'),
                            set())
        self.assertSetEqual(group_links({"d.co/p1"}).get('pages'),
                            {"d.co/p1"})


class DAddictsSpiderTest(TestCase):
    def test_extract_topic_links(self):
        with open('tests/resources/d_addicts_base_page.html') as file:
            links = DAddictsSpider.extract_topic_links(file.read())
            self.assertGreater(len(links), 543)
            for link in links:
                self.assertIn('www.d-addicts.com/forums/viewtopic.php?t=',
                              link)

    def test_extract_links_of_interest(self):
        with open('tests/resources/viewtopic.php?t=99358') as file:
            links = DAddictsSpider.extract_links_of_interest(file.read())
            self.assertGreater(len(links), 8)
            for link in links:
                self.assertIn(DAddictsSpider.file_of_interest_subs, link)

    def test_get_delay(self):  # TODO impl. monad either to test l/r branching
        get_delay = DAddictsSpider.get_delay
        self.assertGreaterEqual(get_delay('http://www.d-addicts.com'), 0)
        with mock.patch('daddicts_spider.Robots', new_callable=FakeRobots):
            self.assertEqual(get_delay('http://www.d-addicts.com'),
                             DAddictsSpider.default_delay)

    def test_next(self):
        daddicts_spider = DAddictsSpider(0)
        self.assertIn('/download/file.php?id=', next(daddicts_spider).pop())
