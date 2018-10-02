from requests_oauthlib import OAuth2Session

from yaml import load, dump, YAMLError
try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper

# OAuth endpoints given in the Google API documentation
authorization_base_url = "https://accounts.google.com/o/oauth2/v2/auth"
# alternative token uri looks nicer
token_uri = "https://www.googleapis.com/oauth2/v4/token"

# scope = [
#    'https://www.googleapis.com/auth/drive.photos.readonly',
#    'https://picasaweb.google.com/data/',
#    'https://www.googleapis.com/auth/drive']

# token_file = '/tmp/testDriveToken'
# secrets_file = '/home/giles/.config/gphotos-sync/client_secret.json'
# drive_api_url = 'https://www.googleapis.com/discovery/v1/apis/drive/v2/rest'


class Authorize:
    def __init__(self, scope, token_file, secrets_file):
        self.scope = scope
        self.token_file = token_file
        self.session = None
        self.token = None
        try:
            stream = open(secrets_file, 'r')
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

    def load_token(self):
        try:
            stream = open(self.token_file, 'r')
            token = load(stream, Loader=Loader)
        except (YAMLError, IOError):
            return None
        return token

    def save_token(self, token):
        stream = open(self.token_file, 'w')
        dump(token, stream, Dumper=Dumper)

    def authorize(self):
        token = self.load_token()

        if token:
            # force refresh on load
            # token.expires_in = -30 # todo this is no longer in the token ?? how to force update?
            self.session = OAuth2Session(self.client_id, token=token,
                                         auto_refresh_url=self.token_uri,
                                         auto_refresh_kwargs=self.extra,
                                         token_updater=self.save_token)
        else:
            print(self.scope)
            self.session = OAuth2Session(self.client_id, scope=self.scope,
                                         redirect_uri=self.redirect_uri,
                                         auto_refresh_url=self.token_uri,
                                         auto_refresh_kwargs=self.extra,
                                         token_updater=self.save_token)

            # Redirect user to Google for authorization
            authorization_url, state = self.session.authorization_url(
                authorization_base_url,
                access_type="offline",
                prompt="select_account")
            print('Please go here and authorize,', authorization_url)

            # Get the authorization verifier code from the callback url
            response_code = input('Paste the full redirect URL here:')

            # Fetch the access token
            self.token = self.session.fetch_token(
                self.token_uri, client_secret=self.client_secret,
                code=response_code)
            self.save_token(self.token)
