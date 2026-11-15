"""Same-origin editor and GitHub App publisher. Run behind HTTPS with Waitress."""
import base64
import hashlib
import hmac
import json
import mimetypes
import os
import re
import secrets
import threading
import time
from dataclasses import dataclass
from http.cookies import SimpleCookie
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, urlencode, urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

from publisher.validation import InvalidDraft, MAX_BYTES, ROOT, validate

REPO = 'oriolroigescobedo/oriolroigescobedo.github.io'
BRANCH = 'feature/portfolio-cms-phase-5'
REF = f'refs/heads/{BRANCH}'
PATH = 'cms/content/published.v3.json'
SESSION_AGE = 1800
LOGIN_AGE = 300
REVIEW_AGE = 600
ASSETS = {'/index.html', '/assets/site.css', '/assets/site.js', '/cms/editor.css', f'/{PATH}',
          '/cms/editor.js', '/cms/advanced.js', '/cms/publish.js', '/cms/content/translations.js'}
SHA = re.compile(r'[a-f0-9]{40}')
HEAD_QUERY = """
query PortfolioDraft($owner: String!, $name: String!, $ref: String!) {
  repository(owner: $owner, name: $name) {
    databaseId viewerPermission
    ref(qualifiedName: $ref) { target { oid } }
  }
}
"""
BLOB_QUERY = """
query PortfolioBlob($owner: String!, $name: String!, $file: String!) {
  repository(owner: $owner, name: $name) {
    object(expression: $file) { ... on Blob { oid } }
  }
}
"""
COMMIT_QUERY = """
mutation PublishPortfolioDraft($input: CreateCommitOnBranchInput!) {
  createCommitOnBranch(input: $input) { commit { oid } }
}
"""


class Problem(Exception):
    def __init__(self, status, message):
        self.status, self.message = status, message


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, *_args, **_kwargs):
        return None


def github(method, url, token=None, data=None, basic=None):
    headers = {'Accept': 'application/json', 'User-Agent': 'Portfolio-CMS-Publisher'}
    if token:
        headers['Authorization'] = f'Bearer {token}'
    if basic:
        headers['Authorization'] = f'Basic {basic}'
    if url.startswith('https://api.github.com/'):
        headers['X-GitHub-Api-Version'] = '2022-11-28'
    if data is not None:
        if url == 'https://github.com/login/oauth/access_token':
            headers['Content-Type'] = 'application/x-www-form-urlencoded'
            data = urlencode(data).encode()
        else:
            headers['Content-Type'] = 'application/json'
            data = json.dumps(data).encode()
    try:
        with build_opener(NoRedirect()).open(Request(url, data, headers, method=method), timeout=15) as response:
            body = response.read(2_000_001)
            if not body:
                return {}
            if len(body) > 2_000_000:
                raise ValueError
            return json.loads(body)
    except HTTPError as error:
        status = error.code
        error.close()
        if status == 401:
            raise Problem(401, 'GitHub authorization expired or was revoked. Connect again.') from None
        if status in (403, 404) and not error.headers.get('Retry-After') and error.headers.get('X-RateLimit-Remaining') != '0':
            raise Problem(403, 'GitHub did not grant access to the development repository.') from None
        raise Problem(502, 'GitHub could not complete the request. Try again shortly.') from None
    except (URLError, OSError, ValueError):
        raise Problem(502, 'GitHub did not return a usable response. Try again shortly.') from None


@dataclass(frozen=True)
class Config:
    origin: str
    client_id: str
    client_secret: str
    user_id: int
    repo_id: int
    installation_id: int

    @classmethod
    def from_env(cls):
        origin = os.environ['CMS_ORIGIN']
        parts = urlsplit(origin)
        if (parts.scheme != 'https' or not parts.hostname or parts.username is not None
                or origin != f'https://{parts.netloc}'):
            raise ValueError('CMS_ORIGIN must be a canonical HTTPS origin without a path.')
        values = [int(os.environ[f'CMS_{key}_ID']) for key in ('USER', 'REPO', 'INSTALLATION')]
        client_id, client_secret = os.environ['CMS_CLIENT_ID'], os.environ['CMS_CLIENT_SECRET']
        if min(values) < 1 or not client_id or not client_secret:
            raise ValueError('Missing or invalid GitHub App configuration.')
        return cls(origin, client_id, client_secret, *values)


@dataclass
class Login:
    expires: float
    state: str
    verifier: str


@dataclass
class Session:
    expires: float
    token: str
    login: str
    review: tuple | None = None


class Publisher:
    def __init__(self, config, request_github=github):
        self.config = config
        self.request_github = request_github
        self.logins, self.sessions = {}, {}
        self.lock = threading.Lock()

    @property
    def callback(self):
        return self.config.origin + '/auth/callback'

    def cookie(self, name, value='', age=0):
        return ('Set-Cookie', f'__Host-cms-{name}={value}; Path=/; Max-Age={age}; Secure; HttpOnly; SameSite=Lax')

    def exchange(self, code, verifier):
        return self.request_github('POST', 'https://github.com/login/oauth/access_token', data={
            'client_id': self.config.client_id, 'client_secret': self.config.client_secret,
            'code': code, 'code_verifier': verifier, 'redirect_uri': self.callback,
            'repository_id': str(self.config.repo_id),
        })

    def revoke(self, token):
        credentials = f'{self.config.client_id}:{self.config.client_secret}'.encode()
        try:
            self.request_github('DELETE', f'https://api.github.com/applications/{self.config.client_id}/token',
                                data={'access_token': token}, basic=base64.b64encode(credentials).decode())
            return True
        except Problem as error:
            return False

    def graph(self, token, query, variables, *, committing=False):
        result = self.request_github('POST', 'https://api.github.com/graphql', token,
                                     {'query': query, 'variables': variables})
        if result.get('errors'):
            # GitHub error payloads may reflect inputs. Return fixed messages only.
            types = {item.get('type') for item in result['errors']}
            if types & {'FORBIDDEN', 'NOT_FOUND', 'INSUFFICIENT_SCOPES', 'UNPROCESSABLE'}:
                if committing:
                    return None  # Check current head to distinguish a stale review.
                raise Problem(403, 'GitHub did not grant access to the development branch.')
            raise Problem(502, 'GitHub did not complete the request. Review again before retrying.')
        return result.get('data')

    def branch(self, session):
        owner, name = REPO.split('/')
        data = self.graph(session.token, HEAD_QUERY, {'owner': owner, 'name': name, 'ref': REF}) or {}
        repo = data.get('repository') or {}
        if repo.get('databaseId') != self.config.repo_id or repo.get('viewerPermission') not in ('ADMIN', 'MAINTAIN', 'WRITE'):
            raise Problem(403, 'The connected account needs write access to this repository.')
        head = ((repo.get('ref') or {}).get('target') or {}).get('oid', '')
        if not SHA.fullmatch(head):
            raise Problem(403, 'The development branch is unavailable.')
        # Resolve the immutable tree so an intervening push cannot affect the comparison.
        data = self.graph(session.token, BLOB_QUERY, {'owner': owner, 'name': name, 'file': f'{head}:{PATH}'}) or {}
        blob = ((data.get('repository') or {}).get('object') or {}).get('oid')
        return head, blob

    def installation_access(self, token):
        result = self.request_github('GET', 'https://api.github.com/user/installations/'
                                     f'{self.config.installation_id}/repositories?per_page=100', token)
        if not any(repo.get('id') == self.config.repo_id and repo.get('full_name', '').lower() == REPO
                   for repo in result.get('repositories', [])):
            raise Problem(403, 'Install the GitHub App on the portfolio repository and reconnect.')

    def dispatch(self, env):
        method, path = env['REQUEST_METHOD'], env['PATH_INFO']
        cookies = SimpleCookie()
        cookies.load(env.get('HTTP_COOKIE', ''))

        def cookie_value(name):
            item = cookies.get(f'__Host-cms-{name}')
            return item.value if item else ''

        now = time.monotonic()
        sid = cookie_value('session')
        with self.lock:
            for store in (self.logins, self.sessions):
                for key in [key for key, value in store.items() if value.expires <= now]:
                    del store[key]
            session = self.sessions.get(sid)

        if method == 'GET' and path == '/auth/callback':
            with self.lock:
                login = self.logins.pop(cookie_value('login'), None)
            query = parse_qs(env.get('QUERY_STRING', ''), max_num_fields=15)
            state, code = query.get('state', ['']), query.get('code', [''])
            headers = [self.cookie('login')]
            outcome = 'failed'
            if (login and len(state) == len(code) == 1 and state[0].isascii()
                    and code[0] and len(code[0]) < 1024 and 'error' not in query
                    and hmac.compare_digest(state[0], login.state)):
                token = None
                try:
                    grant = self.exchange(code[0], login.verifier)
                    token, lifetime = grant.get('access_token'), grant.get('expires_in')
                    if not isinstance(token, str) or grant.get('token_type', '').lower() != 'bearer':
                        raise Problem(401, 'GitHub did not authorize the connection.')
                    if not isinstance(lifetime, int) or lifetime < 1:
                        raise Problem(401, 'Enable expiring user tokens on the GitHub App.')
                    user = self.request_github('GET', 'https://api.github.com/user', token)
                    if user.get('id') != self.config.user_id:
                        raise Problem(403, 'This GitHub account cannot publish.')
                    self.installation_access(token)
                    new_sid = secrets.token_urlsafe(32)
                    with self.lock:
                        self.sessions.pop(sid, None)
                        if len(self.sessions) >= 128:
                            raise Problem(503, 'Too many sessions. Try again shortly.')
                        self.sessions[new_sid] = Session(time.monotonic() + min(lifetime, SESSION_AGE),
                                                         token, user['login'])
                    if session:
                        self.revoke(session.token)
                    headers.append(self.cookie('session', new_sid, min(lifetime, SESSION_AGE)))
                    outcome = 'connected'
                except Problem:
                    if token:
                        self.revoke(token)
            return 303, b'', [*headers, ('Location', f'/auth/{outcome}')]

        if method == 'GET' and path in ('/auth/connected', '/auth/failed'):
            message = ('GitHub connected. Close this tab and check the connection in the editor.'
                       if path.endswith('/connected') and session else
                       'GitHub connection failed. Check the selected account, app installation and token expiry settings.')
            return 200, message.encode(), [('Content-Type', 'text/plain; charset=utf-8')]

        if method == 'GET' and path == '/api/session':
            if session:
                try:
                    user = self.request_github('GET', 'https://api.github.com/user', session.token)
                    if user.get('id') != self.config.user_id:
                        raise Problem(401, 'GitHub authorization is no longer valid.')
                except Problem as error:
                    if error.status != 401:
                        raise
                    with self.lock:
                        self.sessions.pop(sid, None)
                    return 200, {'login': None}, [self.cookie('session')]
            return 200, {'login': session.login if session else None}, []
        if method == 'GET' and not path.startswith('/api/'):
            path = '/index.html' if path == '/' else path
            if path in ASSETS or re.fullmatch(r'/assets/images/image-\d{2}-[a-f0-9]{12}\.(?:png|jpg|svg)', path):
                file = ROOT / path[1:]
                if file.is_file():
                    return 200, file.read_bytes(), [('Content-Type', mimetypes.guess_type(path)[0] or 'application/octet-stream')]

        if method != 'POST' or path not in ('/api/login', '/api/logout', '/api/review', '/api/publish'):
            raise Problem(404, 'Page not found.')
        if env.get('HTTP_ORIGIN') != self.config.origin or env.get('HTTP_X_PORTFOLIO_CMS') != '1':
            raise Problem(403, 'Request origin could not be verified.')
        if env.get('CONTENT_TYPE') != 'application/json':
            raise Problem(415, 'Expected application/json.')

        if path == '/api/login':
            login = Login(now + LOGIN_AGE, secrets.token_urlsafe(32), secrets.token_urlsafe(48))
            key = secrets.token_urlsafe(32)
            with self.lock:
                self.logins.pop(cookie_value('login'), None)
                if len(self.logins) >= 256:
                    raise Problem(503, 'Too many sign-in attempts. Try again shortly.')
                self.logins[key] = login
            challenge = base64.urlsafe_b64encode(hashlib.sha256(login.verifier.encode()).digest()).decode().rstrip('=')
            params = urlencode({'client_id': self.config.client_id, 'redirect_uri': self.callback,
                                'state': login.state, 'code_challenge': challenge, 'code_challenge_method': 'S256',
                                'scope': 'offline_access', 'allow_signup': 'false', 'prompt': 'select_account'})
            return 200, {'url': f'https://github.com/login/oauth/authorize?{params}'}, [self.cookie('login', key, LOGIN_AGE)]
        if path == '/api/logout':
            with self.lock:
                self.sessions.pop(sid, None)
                self.logins.pop(cookie_value('login'), None)
            revoked = self.revoke(session.token) if session else True
            return 200, {'revoked': revoked}, [self.cookie('session'), self.cookie('login')]
        if not session:
            raise Problem(401, 'Connect your GitHub account before reviewing or publishing.')

        try:
            size = int(env.get('CONTENT_LENGTH') or 0)
        except ValueError:
            raise Problem(400, 'Invalid request length.') from None
        if not 0 < size <= MAX_BYTES:
            raise Problem(413, 'Send a JSON draft of up to 12 MB.')
        raw = env['wsgi.input'].read(size)
        if len(raw) != size:
            raise Problem(400, 'Incomplete draft.')
        stored = validate(raw, (self.config.client_secret, session.token))
        digest = hashlib.sha256(stored).digest()
        blob_oid = hashlib.sha1(f'blob {len(stored)}\0'.encode() + stored).hexdigest()
        if path == '/api/review':
            self.installation_access(session.token)
            head, blob = self.branch(session)
            with self.lock:
                if self.sessions.get(sid) is not session or session.expires <= time.monotonic():
                    raise Problem(401, 'Session ended. Connect again.')
                session.review = (digest, head, time.monotonic() + REVIEW_AGE)
            return 200, {'branch': BRANCH, 'path': PATH, 'head': head,
                         'change': 'unchanged' if blob == blob_oid else 'replace' if blob else 'create'}, []

        with self.lock:
            review = session.review
            if (self.sessions.get(sid) is not session or session.expires <= time.monotonic()
                    or not review or review[2] <= time.monotonic() or not hmac.compare_digest(review[0], digest)):
                raise Problem(409, 'Review this exact draft again before publishing.')
            session.review = None
        head, blob = self.branch(session)
        if blob == blob_oid:
            return 200, {'unchanged': True, 'url': f'https://github.com/{REPO}/commit/{head}'}, []
        if head != review[1]:
            raise Problem(409, 'The branch changed. Review the draft again before publishing.')
        data = self.graph(session.token, COMMIT_QUERY, {'input': {
            'branch': {'repositoryNameWithOwner': REPO, 'branchName': BRANCH},
            'expectedHeadOid': head, 'message': {'headline': 'Publish portfolio CMS v3 draft'},
            'fileChanges': {'additions': [{'path': PATH, 'contents': base64.b64encode(stored).decode()}]},
        }}, committing=True) or {}
        oid = ((data.get('createCommitOnBranch') or {}).get('commit') or {}).get('oid', '')
        if not SHA.fullmatch(oid):
            current, _ = self.branch(session)
            if current != head:
                raise Problem(409, 'The branch changed. Review again to check what was saved.')
            raise Problem(403, 'GitHub rejected the commit. Check app permissions and branch rules.')
        return 200, {'unchanged': False, 'url': f'https://github.com/{REPO}/commit/{oid}'}, []

    def __call__(self, env, start_response):
        from http import HTTPStatus

        try:
            status, body, headers = self.dispatch(env)
        except InvalidDraft as error:
            status, body, headers = 422, {'error': str(error)}, []
        except Problem as error:
            status, body, headers = error.status, {'error': error.message}, []
        except Exception:
            # Avoid leaking exception text, OAuth parameters, response bodies or draft content.
            status, body, headers = 500, {'error': 'Publisher error. Try again or check the server configuration.'}, []
        if isinstance(body, dict):
            body = json.dumps(body).encode()
            headers.append(('Content-Type', 'application/json; charset=utf-8'))
        headers += [
            ('Cache-Control', 'no-store'), ('Referrer-Policy', 'no-referrer'),
            ('X-Content-Type-Options', 'nosniff'), ('X-Frame-Options', 'DENY'),
            ('Strict-Transport-Security', 'max-age=31536000'),
            ('Content-Security-Policy', "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; "
             "img-src 'self' data: https:; object-src 'none'; base-uri 'none'; frame-ancestors 'none'; form-action 'none'"),
            ('Content-Length', str(len(body))),
        ]
        start_response(f'{status} {HTTPStatus(status).phrase}', headers)
        return [body]


if __name__ == '__main__':
    from waitress import serve

    serve(Publisher(Config.from_env()), listen='127.0.0.1:8080',
          max_request_body_size=MAX_BYTES, channel_timeout=30, clear_untrusted_proxy_headers=True)
