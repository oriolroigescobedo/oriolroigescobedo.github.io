"""Exercise the real WSGI publisher with a GitHub API double and synthetic drafts."""
import base64
import hashlib
import io
import json
import unittest
from dataclasses import replace
from http.cookies import SimpleCookie
from urllib.parse import parse_qs, urlencode, urlsplit
from wsgiref.util import setup_testing_defaults

from publisher.app import BRANCH, PATH, REF, REPO, Config, Problem, Publisher

ORIGIN = 'https://editor.example.test'
HEAD = '1' * 40
NEW_HEAD = '2' * 40


def draft():
    locales = {locale: {} for locale in ('en', 'es', 'ca', 'fr')}
    return {'version': 3, 'translations': locales, 'static': {}, 'staticLocales': dict(locales),
            'content': {'sections': [{'id': 'home', 'template': 'home', 'entries': []}],
                        'fields': {}, 'attributes': {}, 'links': []}}


class FakeGitHub:
    def __init__(self):
        self.config = Config(ORIGIN, 'app-id', 'test-only-placeholder', 10, 20, 30)
        self.head, self.blob = HEAD, None
        self.user_id, self.permission = 10, 'ADMIN'
        self.installed, self.revoked = True, False
        self.fail_after_commit, self.race, self.deny_commit = False, False, False
        self.grant, self.commits = None, []

    def __call__(self, method, url, token=None, data=None, basic=None):
        if url.endswith('access_token'):
            self.grant = data
            return {'access_token': 'synthetic-session-value', 'token_type': 'bearer', 'expires_in': 3600}
        if method == 'DELETE':
            assert basic and data['access_token'] == 'synthetic-session-value'
            self.revoked = True
            return {}
        if self.revoked:
            raise Problem(401, 'Authorization revoked.')
        if url.endswith('/user'):
            return {'id': self.user_id, 'login': 'account'}
        if '/installations/' in url:
            return {'repositories': [{'id': 20, 'full_name': REPO}] if self.installed else []}
        assert url.endswith('/graphql')
        variables = data['variables']
        if 'query PortfolioDraft' in data['query']:
            assert variables['ref'] == REF
            return {'data': {'repository': {'databaseId': 20, 'viewerPermission': self.permission,
                                           'ref': {'target': {'oid': self.head}}}}}
        if 'PortfolioBlob' in data['query']:
            assert variables['file'] == f'{self.head}:{PATH}'
            return {'data': {'repository': {'object': {'oid': self.blob} if self.blob else None}}}
        value = variables['input']
        assert value['branch'] == {'repositoryNameWithOwner': REPO, 'branchName': BRANCH}
        assert set(value['fileChanges']) == {'additions'}
        change, = value['fileChanges']['additions']
        assert change['path'] == PATH
        if self.race:
            self.head = NEW_HEAD
        if self.deny_commit or value['expectedHeadOid'] != self.head:
            return {'errors': [{'type': 'UNPROCESSABLE', 'message': 'Internal GitHub details'}]}
        raw = base64.b64decode(change['contents'])
        self.blob = hashlib.sha1(f'blob {len(raw)}\0'.encode() + raw).hexdigest()
        self.commits.append(raw)
        self.head = NEW_HEAD
        if self.fail_after_commit:
            raise Problem(502, 'GitHub response could not be received.')
        return {'data': {'createCommitOnBranch': {'commit': {'oid': NEW_HEAD}}}}


class PublisherTests(unittest.TestCase):
    def setUp(self):
        self.github = FakeGitHub()
        self.app = Publisher(self.github.config, self.github)
        self.cookies = SimpleCookie()

    def request(self, path, body=None, *, raw=None, headers=None):
        parsed = urlsplit(path)
        env = {'PATH_INFO': parsed.path, 'QUERY_STRING': parsed.query,
               'REQUEST_METHOD': 'GET', 'HTTP_COOKIE': self.cookies.output(header='', sep=';').strip()}
        if body is not None or raw is not None:
            raw = raw if raw is not None else json.dumps(body).encode()
            env.update(REQUEST_METHOD='POST', CONTENT_TYPE='application/json', CONTENT_LENGTH=str(len(raw)),
                       HTTP_ORIGIN=ORIGIN, HTTP_X_PORTFOLIO_CMS='1', **{'wsgi.input': io.BytesIO(raw)})
        env.update(headers or {})
        setup_testing_defaults(env)
        result = []
        response, = self.app(env, lambda status, fields: result.extend((int(status.split()[0]), fields)))
        status, fields = result
        for key, value in fields:
            if key == 'Set-Cookie':
                self.assertIn('Secure; HttpOnly; SameSite=Lax', value)
                changed = SimpleCookie(value)
                cookie, = changed.values()
                if cookie.value:
                    self.cookies[cookie.key] = cookie.value
                else:
                    self.cookies.pop(cookie.key, None)
        data = json.loads(response) if dict(fields).get('Content-Type', '').startswith('application/json') else response
        return status, data, dict(fields)

    def start_login(self):
        status, data, _ = self.request('/api/login', {})
        self.assertEqual(status, 200)
        self.assertEqual(urlsplit(data['url']).netloc, 'github.com')
        return {key: val[0] for key, val in parse_qs(urlsplit(data['url']).query).items()}

    def callback(self, state):
        return self.request('/auth/callback?' + urlencode({'state': state, 'code': 'fixture-code'}))

    def login(self):
        params = self.start_login()
        status, _, headers = self.callback(params['state'])
        self.assertEqual((status, headers['Location']), (303, '/auth/connected'))
        challenge = base64.urlsafe_b64encode(hashlib.sha256(self.github.grant['code_verifier'].encode()).digest())
        self.assertEqual(challenge.decode().rstrip('='), params['code_challenge'])
        self.assertEqual(self.github.grant['repository_id'], '20')
        self.assertEqual(params['code_challenge_method'], 'S256')
        self.assertEqual(self.request('/api/session')[1], {'login': 'account'})
        return params

    def test_login_rejects_invalid_state_and_replay(self):
        params = self.start_login()
        self.assertEqual(self.callback('wrong')[2]['Location'], '/auth/failed')
        self.assertIsNone(self.github.grant)
        self.assertEqual(self.callback(params['state'])[2]['Location'], '/auth/failed')
        params = self.login()
        self.assertEqual(self.callback(params['state'])[2]['Location'], '/auth/failed')
        self.assertEqual(self.request('/api/session')[1], {'login': 'account'})

    def test_login_denies_other_accounts_and_missing_installation(self):
        for user_id, installed in ((11, True), (10, False)):
            self.github.user_id, self.github.installed, self.github.revoked = user_id, installed, False
            self.assertEqual(self.callback(self.start_login()['state'])[2]['Location'], '/auth/failed')
            self.assertTrue(self.github.revoked)
            self.assertEqual(self.request('/api/session')[1], {'login': None})

    def test_origin_media_type_and_session_required(self):
        self.assertEqual(self.request('/api/review', draft())[0], 401)
        self.assertEqual(self.request('/api/login', {}, headers={'HTTP_ORIGIN': 'https://other.test'})[0], 403)
        self.assertEqual(self.request('/api/login', {}, headers={'HTTP_X_PORTFOLIO_CMS': ''})[0], 403)
        self.assertEqual(self.request('/api/login', {}, headers={'CONTENT_TYPE': 'text/plain'})[0], 415)
        self.assertEqual(self.request('/publisher/app.py')[0], 404)
        self.login()
        self.github.permission = 'READ'
        self.assertEqual(self.request('/api/review', draft())[0], 403)

    def test_logout_revocation_and_expiry(self):
        self.login()
        sid = self.cookies['__Host-cms-session'].value
        self.assertEqual(self.request('/api/logout', {})[1], {'revoked': True})
        self.cookies['__Host-cms-session'] = sid
        self.assertEqual(self.request('/api/publish', draft())[0], 401)
        self.github.revoked = False
        self.login()
        sid = self.cookies['__Host-cms-session'].value
        self.app.sessions[sid] = replace(self.app.sessions[sid], expires=0)
        self.assertEqual(self.request('/api/session')[1], {'login': None})
        self.login()
        self.github.revoked = True
        self.assertEqual(self.request('/api/session')[1], {'login': None})

    def test_commit_is_reviewed_once_and_touches_only_the_draft(self):
        self.login()
        pending = draft()
        self.assertEqual(self.request('/api/publish', pending)[0], 409)
        status, review, _ = self.request('/api/review', pending)
        self.assertEqual((status, review), (200, {'branch': BRANCH, 'path': PATH, 'head': HEAD, 'change': 'create'}))
        modified = draft()
        modified['content']['fields']['home:0'] = {'ca': 'Revisió'}
        self.assertEqual(self.request('/api/publish', modified)[0], 409)
        published = self.request('/api/publish', pending)
        self.assertEqual(published[0], 200)
        self.assertTrue(published[1]['url'].endswith(NEW_HEAD))
        self.assertEqual([json.loads(raw) for raw in self.github.commits], [pending])
        self.assertEqual(self.request('/api/publish', pending)[0], 409)
        self.assertEqual(self.request('/api/review', pending)[1]['change'], 'unchanged')
        self.assertTrue(self.request('/api/publish', pending)[1]['unchanged'])
        self.assertEqual(len(self.github.commits), 1)
        self.assertEqual(self.request('/api/review', modified)[1]['change'], 'replace')

    def test_conflict_permission_rejection_and_ambiguous_network_failure(self):
        self.login()
        pending = draft()
        self.request('/api/review', pending)
        self.github.race = True
        self.assertEqual(self.request('/api/publish', pending)[0], 409)
        self.assertFalse(self.github.commits)
        self.github.race = False
        self.request('/api/review', pending)
        self.github.deny_commit = True
        rejected = self.request('/api/publish', pending)
        self.assertEqual(rejected[0], 403)
        self.assertNotIn('Internal GitHub details', repr(rejected))
        self.github.deny_commit = False
        self.request('/api/review', pending)
        self.github.fail_after_commit = True
        self.assertEqual(self.request('/api/publish', pending)[0], 502)
        self.assertEqual(self.request('/api/review', pending)[1]['change'], 'unchanged')
        self.assertEqual(len(self.github.commits), 1)

    def test_invalid_content_and_credentials_are_rejected_without_echoing_values(self):
        self.login()
        for value in ('<mark>unsupported</mark>', '<a href="ftp://example.test">link</a>',
                      self.github.config.client_secret, 'synthetic-session-value',
                      'github' + '_pat_' + 'X'*24, 'pass' + 'word=EXAMPLEONLY'):
            pending = draft()
            pending['content']['fields']['home:0'] = {'en': value}
            rejected = self.request('/api/review', pending)
            self.assertEqual(rejected[0], 422)
            self.assertNotIn(value, repr(rejected))
        pending = draft()
        pending['content']['sections'][0]['id'] = 'other'
        self.assertEqual(self.request('/api/review', pending)[0], 422)
        self.assertEqual(self.request('/api/review', raw=b'{"version":3,"version":3}')[0], 422)
        self.assertEqual(self.request('/api/review', raw=b'x' * 12_000_001)[0], 413)
        self.assertFalse(self.github.commits)


if __name__ == '__main__':
    unittest.main()
