from requests.adapters import HTTPAdapter
from requests_oauthlib import OAuth2Session
from urllib3.util.retry import Retry
from typing import List, Optional
import os

from yaml import load, dump, YAMLError

try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper

# OAuth endpoints given in the Google API documentation
authorization_base_url = "https://accounts.google.com/o/oauth2/v2/auth"
token_uri = "https://www.googleapis.com/oauth2/v4/token"


class Authorize:
    def __init__(self, scope: List[str], token_file: str, secrets_file: str):
        """ A very simple class to handle Google API authorization flow
        for the requests library. Includes saving the token and automatic
        token refresh.

        Args:
            scope: list of the scopes for which permission will be granted
            token_file: full path of a file in which the user token will be
            placed. After first use the previous token will also be read in from
            this file
            secrets_file: full path of the client secrets file obtained from
            Google Api Console
        """
        self.scope = scope
        self.token_file = token_file
        self.session = None
        self.token = None
        try:
            with open(secrets_file, 'r') as stream:
                all_yaml = load(stream, Loader=Loader)
            secrets = all_yaml['installed']
            self.client_id = secrets['client_id']
            self.client_secret = secrets['client_secret']
            self.redirect_uri = secrets['redirect_uris'][0]
            self.token_uri = secrets['token_uri']
            self.extra = {
                'client_id': self.client_id,
                'client_secret': self.client_secret}

        except (YAMLError, IOError):
            print('missing or bad secrets file: {}'.format(secrets_file))
            exit(1)

    def load_token(self) -> Optional[str]:
        try:
            with open(self.token_file, 'r') as stream:
                token = load(stream, Loader=Loader)
        except (YAMLError, IOError):
            return None
        return token

    def save_token(self, token: str):
        with open(self.token_file, 'w') as stream:
            dump(token, stream, Dumper=Dumper)
        os.chmod(self.token_file, 0o600)

    def authorize(self):
        """ Initiates OAuth2 authentication and authorization flow
        """
        token = self.load_token()

        if token:
            self.session = OAuth2Session(self.client_id, token=token,
                                         auto_refresh_url=self.token_uri,
                                         auto_refresh_kwargs=self.extra,
                                         token_updater=self.save_token)
        else:
            self.session = OAuth2Session(self.client_id, scope=self.scope,
                                         redirect_uri=self.redirect_uri,
                                         auto_refresh_url=self.token_uri,
                                         auto_refresh_kwargs=self.extra,
                                         token_updater=self.save_token)

            # Redirect user to Google for authorization
            authorization_url, _ = self.session.authorization_url(
                authorization_base_url,
                access_type="offline",
                prompt="select_account")
            print('Please go here and authorize,', authorization_url)

            # Get the authorization verifier code from the callback url
            response_code = input('Paste the response token here:')

            # Fetch the access token
            self.token = self.session.fetch_token(
                self.token_uri, client_secret=self.client_secret,
                code=response_code)
            self.save_token(self.token)

        # note we want retries on POST as well, need to review this once we
        # start to do methods that write to Google Photos
        retries = Retry(total=5,
                        backoff_factor=0.1,
                        status_forcelist=[500, 502, 503, 504],
                        method_whitelist=frozenset(['GET', 'POST']),
                        raise_on_status=False)
        self.session.mount('https://', HTTPAdapter(max_retries=retries))
