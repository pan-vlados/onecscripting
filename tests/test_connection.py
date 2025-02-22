import configparser
import logging
import unittest
from contextlib import contextmanager
from pathlib import Path

from src.onecscripting.infobase import OneC


TEST_CONFIG_FILENAME = 'test_config.ini'
logging.basicConfig(
    format='[%(levelname)s] %(asctime)s - %(message)s',
    datefmt='%d.%m.%Y %H:%M',
    level=logging.CRITICAL,
)
logger = logging.getLogger(__name__)


class TestConnection(unittest.TestCase):
    @classmethod
    def setUp(cls):
        config = configparser.ConfigParser()
        config.read(Path(__file__).absolute().parent / TEST_CONFIG_FILENAME)
        cls.config_dbtest = dict(config.items('DBTEST'))
        cls.onec = OneC()

    @contextmanager
    def assertNotRaises(
        self, exc_type
    ):  # example from https://gist.github.com/hzlmn/6b7bc384301afefcac6de3829bd4c032
        try:
            yield None
        except Exception as ex:
            raise self.failureException(ex)

    # @unittest.skip('Skipped')
    def test_connect(self):
        with self.assertNotRaises(Exception):
            with self.onec.connect(**self.config_dbtest):
                pass

    # @unittest.skip('Skipped')
    def test_async_connect(self):
        def job_test_connect(system, settings):
            with system.connect(**settings):
                pass

        from concurrent.futures import ThreadPoolExecutor

        with ThreadPoolExecutor(max_workers=2) as executor:
            foo = executor.submit(job_test_connect, self.onec, self.config_dbtest)
        results = [foo.result()]


if __name__ == '__main__':
    unittest.main(verbosity=2)
