import sys
import io
import uuid

from unittest import mock, TestCase

from reppy.robots import Robots
from reppy.exceptions import ReppyException

from lib.monad.either import Left, Right

from daddicts_spider import *


class FakeRobots():
    def fetch(self, url):
        raise ReppyException({'obj': self, 'url': url})


class FakeCliArgs():
    def __init__(self, delay, take):
        self.delay = delay
        self.take = take


class TopLevelTest(TestCase):
    def test_unsorted_group_by(self):
        tag_file_or_page_link = ABCSpider.tag_file_or_page_link
        links = {"d.com/1file.php?id=", "d.com/page1", "d.com/page2"}
        self.assertCountEqual(unsorted_group_by(links, tag_file_or_page_link),
                              {'subs': ["d.com/1file.php?id="],
                               'pages': ["d.com/page1", "d.com/page2"]})

    def test_main(self):
        cli_args = FakeCliArgs('0', '2')
        stdout_ = sys.stdout
        sys.stdout = io.StringIO()
        main(cli_args)
        main_out = sys.stdout.getvalue()
        sys.stdout = stdout_
        link_common_part = 'http://www.d-addicts.com/forums/download/file.php?id='
        self.assertGreaterEqual(main_out.count(link_common_part), 2)


class PathTest(TestCase):
    def test_is_file_with_content(self):
        path = Path(str(uuid.uuid4()))
        self.assertFalse(path.is_file_with_content())
        path.touch()
        self.assertFalse(path.is_file_with_content())
        path.write_text('random content')
        self.assertTrue(path.is_file_with_content())
        path.unlink()


class FilePersistableSetTest(TestCase):
    def test_repr(self):
        rand_filename = str(uuid.uuid4())
        file_persistable_set = FilePersistableSet(rand_filename, set())
        file_persistable_set_repr = repr(file_persistable_set)
        self.assertEqual(file_persistable_set_repr, "")
        file_persistable_set = FilePersistableSet(rand_filename, {1})
        file_persistable_set_repr = repr(file_persistable_set)
        self.assertEqual(file_persistable_set_repr, '{1}')

    def integration_test(self):
        rand_filename = str(uuid.uuid4())
        file_persistable_set = FilePersistableSet(rand_filename, {1, 2})
        self.assertFalse(file_persistable_set.retrieve())
        file_persistable_set.persist()
        self.assertEqual(file_persistable_set.retrieve(), {1, 2})
        Path(rand_filename).unlink()


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


class ABCSpiderTest(TestCase):
    def test_tag_file_or_page_link(self):
        tag_file_or_page_link = ABCSpider.tag_file_or_page_link
        self.assertEqual(tag_file_or_page_link('d.com/file.php?id='), 'subs')
        self.assertEqual(tag_file_or_page_link('d.com/page1'), 'pages')

    def test_group_links(self):
        group_links = ABCSpider.group_links
        self.assertSetEqual(group_links({"d.co/p1"}).get('subs'), set())
        self.assertSetEqual(group_links({"d.co/file.php?id="}).get('pages'), set())
        self.assertSetEqual(group_links({"d.co/p1"}).get('pages'), {"d.co/p1"})

    def test_robots_delay(self):  # TODO impl. monad either to test l/r branch
        get_robots_delay = ABCSpider.get_robots_delay
        robots_delay = get_robots_delay('http://www.d-addicts.com')
        self.assertTrue(isinstance(robots_delay, Right))
        self.assertGreaterEqual(robots_delay.getValue(), 0)
        with mock.patch('daddicts_spider.Robots', new_callable=FakeRobots):
            self.assertEqual(get_robots_delay('http://www.d-addicts.com'), Left(None))

    def test_choose_delay(self):
        get_robots_delay = ABCSpider.get_robots_delay
        choose_delay = ABCSpider.choose_delay
        default_delay = ABCSpider.default_delay
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

    def test_complete_link(self):
        rel_link = './download/file.php?id=51885&sid=09fccbbc6636ee1d35b7f021384574ce'
        link = 'http://www.d-addicts.com/forums/download/file.php?id=51885'
        self.assertEqual(DAddictsSpider.complete_link(rel_link), link)

    def test_next(self):
        self.assertIn('/download/file.php?id=', next(DAddictsSpider(0)).pop())
