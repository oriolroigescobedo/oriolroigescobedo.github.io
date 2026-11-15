"""Render entry point for the development publisher."""
import os

from waitress import serve

from publisher.app import BRANCH, MAX_BYTES, Config, Publisher


def setup_pending(_env, start_response):
    body = b'Portfolio CMS development server. GitHub App setup is pending.\n'
    start_response('200 OK', [
        ('Content-Type', 'text/plain; charset=utf-8'),
        ('Content-Length', str(len(body))),
        ('Cache-Control', 'no-store'),
        ('X-Content-Type-Options', 'nosniff'),
    ])
    return [body]


if __name__ == '__main__':
    if os.environ['RENDER_GIT_BRANCH'] != BRANCH:
        raise SystemExit(f'The Render service must use {BRANCH}.')
    os.environ.setdefault('CMS_ORIGIN', os.environ['RENDER_EXTERNAL_URL'])
    credentials = ('CMS_CLIENT_ID', 'CMS_CLIENT_SECRET', 'CMS_USER_ID', 'CMS_REPO_ID', 'CMS_INSTALLATION_ID')
    app = Publisher(Config.from_env()) if all(os.environ.get(key) for key in credentials) else setup_pending
    serve(app, listen=f"0.0.0.0:{int(os.environ['PORT'])}", max_request_body_size=MAX_BYTES,
          channel_timeout=30, clear_untrusted_proxy_headers=True)
