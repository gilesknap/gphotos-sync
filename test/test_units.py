from _datetime import datetime
import os
from requests.exceptions import ConnectionError
from unittest import TestCase
import gphotos.authorize as auth

scope = [
    'https://www.googleapis.com/auth/photoslibrary.readonly',
    'https://www.googleapis.com/auth/photoslibrary.sharing',
]

token_file = os.path.join(os.path.dirname(os.path.abspath(
    __file__)), 'test_credentials', '.gphotos.token')

secrets_file = os.path.join(os.path.dirname(os.path.abspath(
    __file__)), 'test_credentials', 'client_secret.json')


class TestUnits(TestCase):
    def test_http_500_retries(self):
        a = auth.Authorize(scope, token_file, secrets_file)
        a.authorize()

        start = datetime.now()

        result = a.session.get('https://httpbin.org/status/500',
                               timeout=10)
        self.assertEquals(result.status_code, 500)
        elapsed = datetime.now() - start
        # timeout should not affect the 5 retries
        self.assertLess(elapsed.seconds, 10)

    def test_download_timeout(self):
        a = auth.Authorize(scope, token_file, secrets_file)
        a.authorize()
        retry_error = False
        start = datetime.now()

        try:
            _ = a.session.get('https://httpbin.org//delay/5',
                              stream=True,
                              timeout=.2)
        except ConnectionError as e:
            retry_error = True
            print(e)

        elapsed = datetime.now() - start
        print('timeout elapsed %d'.format(elapsed.seconds))
        self.assertEquals(retry_error, True)
        # .2 timeout by 5 retries = 1 sec
        self.assertGreater(elapsed.seconds, 1)
