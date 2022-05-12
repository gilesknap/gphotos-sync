import logging
from datetime import datetime
from unittest import TestCase

from requests import Session, exceptions
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

log = logging.getLogger(__name__)


class TestRequests(TestCase):
    """
    (Not testing code in this project)
    This is just testing my understanding of retry and exceptions in
    requests / urllib3. It was not easy to work out what exceptions to
    expect so I'm keeping this code as a reminder.
    """

    def test_retries_500(self):
        retries = 5
        timeout = 2

        session = Session()
        start = datetime.now()
        result = session.get("https://httpbin.org/status/500", timeout=timeout)
        self.assertEqual(result.status_code, 500)
        elapsed = datetime.now() - start

        retry = Retry(
            total=retries,
            backoff_factor=0.1,
            status_forcelist=[500, 502, 503, 504],
            allowed_methods=frozenset(["GET", "POST"]),
            raise_on_status=False,
            respect_retry_after_header=True,
        )

        session.close()
        session.mount("https://", HTTPAdapter(max_retries=retry))

        start = datetime.now()
        result = session.get("https://httpbin.org/status/500", timeout=timeout)
        elapsed2 = datetime.now() - start
        self.assertEqual(result.status_code, 500)
        self.assertGreater(elapsed2, elapsed * (retries - 1))
        session.close()

    def test_retries_timeout(self):
        retries = 3
        timeout = 1
        retry_error = False

        session = Session()
        retry = Retry(
            total=retries,
            backoff_factor=0.1,
            status_forcelist=[500, 502, 503, 504],
            allowed_methods=frozenset(["GET", "POST"]),
            raise_on_status=False,
            respect_retry_after_header=True,
        )

        session.mount("https://", HTTPAdapter(max_retries=retry))

        start = datetime.now()
        try:
            _ = session.get("https://httpbin.org/delay/5", timeout=timeout)
        except exceptions.ConnectionError as e:
            retry_error = True
            print(e)

        elapsed = datetime.now() - start
        self.assertEqual(retry_error, True)
        self.assertGreater(elapsed.seconds, retries * timeout)
