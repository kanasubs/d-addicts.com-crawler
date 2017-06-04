import sys
import io

from unittest import mock, TestCase

from reppy.robots import Robots
from reppy.exceptions import ReppyException

from daddicts_spider import *

from util.monad.either import Left, Right


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

    def test_main(self):
        stdout_ = sys.stdout
        sys.stdout = io.StringIO()
        main(['daddicts_spider', '0', '2'])
        main_out = sys.stdout.getvalue()
        sys.stdout = stdout_
        self.assertGreaterEqual(main_out.count('./download/file.php?id='), 2)


class FileLinkStoreTest(TestCase):
    def test_file_link_store_update(self):
        file_link_store = FileLinkStore()
        links = file_link_store.update({'d.co/file.php?id=1'})
        self.assertSetEqual(links, {'d.co/file.php?id=1'})
        links = file_link_store.update({'d.co/file.php?id=1', 'd.co/file.php?id=2'})
        self.assertSetEqual(links, {'d.co/file.php?id=2'})

    def test_file_link_store_can_take(self):
        can_always_take_file_link_store = FileLinkStore()
        self.assertTrue(can_always_take_file_link_store)
        can_take_file_link_store = FileLinkStore(1)
        self.assertTrue(can_take_file_link_store.can_take())
        cant_take_file_link_store = FileLinkStore(0)
        self.assertFalse(cant_take_file_link_store.can_take())


class AbstractSpiderTest(TestCase):
    def test_tag_file_or_page_link(self):
        tag_file_or_page_link = AbstractSpider.tag_file_or_page_link
        self.assertEqual(tag_file_or_page_link('d.com/file.php?id='), 'subs')
        self.assertEqual(tag_file_or_page_link('d.com/page1'), 'pages')

    def test_group_links(self):
        group_links = AbstractSpider.group_links
        self.assertSetEqual(group_links({"d.co/p1"}).get('subs'), set())
        self.assertSetEqual(group_links({"d.co/file.php?id="}).get('pages'), set())
        self.assertSetEqual(group_links({"d.co/p1"}).get('pages'), {"d.co/p1"})

    def test_robots_delay(self):  # TODO impl. monad either to test l/r branch
        get_robots_delay = AbstractSpider.get_robots_delay
        robots_delay = get_robots_delay('http://www.d-addicts.com')
        self.assertTrue(isinstance(robots_delay, Right))
        self.assertGreaterEqual(robots_delay.getValue(), 0)
        with mock.patch('daddicts_spider.Robots', new_callable=FakeRobots):
            self.assertEqual(get_robots_delay('http://www.d-addicts.com'), Left(None))

    def test_choose_delay(self):
        get_robots_delay = AbstractSpider.get_robots_delay
        choose_delay = AbstractSpider.choose_delay
        default_delay = AbstractSpider.default_delay
        self.assertEqual(choose_delay(0, 'http://www.d-addicts.com'), Right(0))
        self.assertEqual(choose_delay(None, 'http://www.d-addicts.com').getValue(),
                         get_robots_delay('http://www.d-addicts.com').getValue())
        self.assertEqual(choose_delay(0, 'bad_website'), Right(0))
        self.assertEqual(choose_delay(None, 'bad_website'), Left(default_delay))


class DAddictsSpiderTest(TestCase):
    def test_extract_topic_links(self):
        filename = 'tests/resources/d_addicts_base_page.html'
        with open(filename, encoding='UTF-8') as file:
            links = DAddictsSpider.extract_topic_links(file.read())
            self.assertGreater(len(links), 543)
            for link in links:
                self.assertIn('www.d-addicts.com/forums/viewtopic.php?t=', link)

    def test_extract_links_of_interest(self):
        filename = 'tests/resources/viewtopic.php?t=99358'
        with open(filename, encoding='UTF-8') as file:
            links = DAddictsSpider.extract_links_of_interest(file.read())
            self.assertGreater(len(links), 8)
            for link in links:
                self.assertIn(DAddictsSpider.file_of_interest_subs, link)

    def test_next(self):
        self.assertIn('/download/file.php?id=', next(DAddictsSpider(0)).pop())


class MainSpiderTest(TestCase):
    def test_maybe_get_delay(self):
        maybe_get_delay = MainSpider.maybe_get_delay
        self.assertIsNone(maybe_get_delay(['daddicts_spider']))
        self.assertEqual(maybe_get_delay(['daddicts_spider', '6']), 6)
