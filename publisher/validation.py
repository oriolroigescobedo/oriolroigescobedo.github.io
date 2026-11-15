"""Validate the editor's v3 envelope before creating a repository commit."""
import base64
import html
import json
import re
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
MAX_BYTES = 12_000_000
SCHEMA = Draft202012Validator(json.loads((ROOT / 'cms/content.schema.json').read_text(encoding='utf8')))
TRANSLATIONS = json.loads((ROOT / 'cms/content/translations.json').read_text(encoding='utf8'))
BASE_ENTRIES = {'home': 0, 'about': 0, 'education': 6, 'experience': 6, 'personal': 5, 'contact': 0}
TEMPLATES = {f'{section}-entry-{i}': section for section, count in BASE_ENTRIES.items() for i in range(count)}
TARGET_PREFIXES = {*BASE_ENTRIES, *(f'chrome-{i}' for i in range(4))}
SECRET = re.compile(
    r'-----BEGIN [A-Z0-9 ]*PRIVATE KEY-----|'
    r'\b(?:gh[pousr]_[a-z0-9_]{16,}|github_pat_[a-z0-9_]{16,}|'
    r'(?:AKIA|ASIA)[A-Z0-9]{16}|xox[baprs]-[a-z0-9-]{12,}|'
    r'sk-(?:proj-)?[a-zA-Z0-9_-]{20,}|AIza[a-z0-9_-]{30,})\b|'
    r'\b(?:password|client[_ -]?secret|api[_ -]?key|access[_ -]?token|authorization)'
    r'\s*[:=]\s*["\']?(?:bearer\s+)?[^\s<>&"\']{8,}', re.I)


class InvalidDraft(ValueError):
    pass


def strict_json(raw):
    def object_pairs(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise InvalidDraft('Duplicate JSON keys are not supported.')
            result[key] = value
        return result

    def constant(_):
        raise InvalidDraft('Invalid JSON number.')

    try:
        return json.loads(raw.decode('utf-8'), object_pairs_hook=object_pairs, parse_constant=constant)
    except (UnicodeError, ValueError, RecursionError):
        raise InvalidDraft('Expected valid UTF-8 JSON with unique keys.') from None


def check_secrets(value, credentials):
    for _ in range(3):
        if SECRET.search(value) or any(secret and secret in value for secret in credentials):
            raise InvalidDraft('A credential-like value was detected. Remove it before reviewing.')
        decoded = unquote(html.unescape(value))
        if decoded == value:
            break
        value = decoded


def url(value, image=False, credentials=()):
    if image and value.startswith('data:'):
        match = re.fullmatch(r'data:image/(png|jpeg|gif|webp);base64,([A-Za-z0-9+/=]+)', value)
        if match and len(match[2]) <= 2_666_668:
            try:
                raw = base64.b64decode(match[2], validate=True)
            except ValueError:
                raw = b''
            signatures = {'png': b'\x89PNG\r\n\x1a\n', 'jpeg': b'\xff\xd8\xff', 'gif': b'GIF', 'webp': b'RIFF'}
            if (len(raw) <= 2_000_000 and raw.startswith(signatures[match[1]])
                    and (match[1] != 'webp' or raw[8:12] == b'WEBP')):
                check_secrets(raw.decode('latin-1'), credentials)
                return
        raise InvalidDraft('Invalid raster image upload.')
    if not value or len(value) > 4096 or re.search(r'[\x00-\x20\x7f\\]|\s', value):
        raise InvalidDraft('Invalid image or link URL.')
    try:
        parts = urlsplit(value)
        if parts.scheme in ('http', 'https') and parts.hostname and parts.username is None:
            parts.port  # Check syntax and range.
            return
    except ValueError:
        raise InvalidDraft('Invalid image or link URL.') from None
    if not parts.scheme and re.match(r'^(?:\./|\.\./|/(?!/)|assets/)', value):
        if not re.search(r'[\\\x00-\x20]|^//', unquote(value)):
            return
    if not image and (value.startswith('#') or parts.scheme in ('mailto', 'tel') and parts.path):
        return
    raise InvalidDraft('Unsupported image or link URL.')


class RichText(HTMLParser):
    tags = {'p', 'br', 'strong', 'b', 'em', 'i', 'u', 'span', 'a', 'div'}
    classes = {'name-accent', 'brand-word', 'brand-guspira', 'brand-accenture', 'brand-upc', 'brand-upf'}

    def __init__(self, allow_year):
        super().__init__(convert_charrefs=True)
        self.allow_year = allow_year
        self.text = []

    def handle_starttag(self, tag, pairs):
        attrs = dict(pairs)
        if tag not in self.tags or len(attrs) != len(pairs) or None in attrs.values():
            self.invalid()
        if tag == 'span':
            if (attrs.keys() - {'class', 'id'} or set(attrs.get('class', '').split()) - self.classes
                    or 'id' in attrs and (not self.allow_year or attrs['id'] != 'year')):
                self.invalid()
        elif tag == 'a':
            if (attrs.keys() - {'href', 'target', 'rel'} or
                    (('target' in attrs or 'rel' in attrs)
                     and (attrs.get('target'), attrs.get('rel')) != ('_blank', 'noopener noreferrer'))):
                self.invalid()
            if 'href' in attrs:
                url(attrs['href'])
        elif attrs:
            self.invalid()

    def handle_endtag(self, tag):
        if tag not in self.tags:
            self.invalid()

    def handle_data(self, value):
        self.text.append(value)

    @staticmethod
    def invalid(*_):
        raise InvalidDraft('Rich text contains unsupported markup or attributes.')

    handle_comment = handle_decl = handle_pi = unknown_decl = invalid


def validate(raw, credentials=()):
    draft = strict_json(raw)
    try:
        valid = SCHEMA.is_valid(draft)
    except RecursionError:
        valid = False
    if not valid:
        raise InvalidDraft('The draft does not match the version 3 schema.')

    def secret_scan(value):
        if isinstance(value, str):
            check_secrets(value, credentials)
        elif isinstance(value, dict):
            for key, child in value.items():
                if key in ('__proto__', 'prototype', 'constructor'):
                    raise InvalidDraft('Invalid draft key.')
                check_secrets(key, credentials)
                secret_scan(child)
        elif isinstance(value, list):
            for child in value:
                secret_scan(child)

    secret_scan(draft)

    def rich(value, allow_year=False):
        if len(value) >= 100_000:
            raise InvalidDraft('A rich-text field is too large.')
        parser = RichText(allow_year)
        parser.feed(value)
        parser.close()
        check_secrets(''.join(parser.text), credentials)

    for locale, fields in draft['translations'].items():
        for key, value in fields.items():
            if key not in TRANSLATIONS[locale]:
                raise InvalidDraft('Unknown translation field.')
            rich(value, key == 'footerCopy')
    for fields in draft['staticLocales'].values():
        for key, value in fields.items():
            if not re.fullmatch(r's:[#a-zA-Z0-9_>():-]{1,250}', key):
                raise InvalidDraft('Invalid static field reference.')
            rich(value)

    content = draft['content']
    used = set()
    targets = set(TARGET_PREFIXES)

    def claim(id_):
        if id_ in used:
            raise InvalidDraft('Duplicate section, entry or link ID.')
        used.add(id_)

    for section in content['sections']:
        id_ = section['id']
        claim(id_)
        if id_ in BASE_ENTRIES:
            if section['template'] != id_ or (not BASE_ENTRIES[id_] and section['entries']):
                raise InvalidDraft('Invalid original section template.')
        elif not id_.startswith('cms-') or section['template'] != 'custom':
            raise InvalidDraft('Unknown section template.')
        targets.add(id_)
        for entry in section['entries']:
            entry_id, template = entry['id'], entry['template']
            claim(entry_id)
            if template not in TEMPLATES or (entry_id in TEMPLATES and
                    (entry_id != template or TEMPLATES[entry_id] != id_)) or (
                    entry_id not in TEMPLATES and not entry_id.startswith('cms-')):
                raise InvalidDraft('Invalid entry template.')
            if entry_id.startswith('cms-'):
                targets.add(entry_id)
    if 'home' not in used:
        raise InvalidDraft('The home section is required.')

    def target(key):
        prefix, _, route = key.partition(':')
        # Deleted custom components can retain overrides in existing v3 drafts.
        if (prefix not in targets and not re.fullmatch(r'cms-[a-z0-9_-]{1,87}', prefix)
                or not re.fullmatch(r'[a-zA-Z0-9_.-]{0,198}', route) or ':' not in key or len(key) > 200):
            raise InvalidDraft('Invalid component field reference.')

    for key, fields in content['fields'].items():
        target(key)
        for value in fields.values():
            rich(value)
    for key, attrs in content['attributes'].items():
        target(key)
        if 'href' in attrs:
            url(attrs['href'])
        if 'src' in attrs:
            url(attrs['src'], image=True, credentials=credentials)
        if any(len(value) > 1000 for value in attrs.get('alt', {}).values()):
            raise InvalidDraft('An image description is too long.')
    for link in content['links']:
        if not re.fullmatch(r'cms-[a-z0-9_-]{1,87}', link['id']):
            raise InvalidDraft('Invalid link ID.')
        claim(link['id'])
        target(link['owner'])
        url(link['href'])
        if any(len(value) > 500 for value in link['label'].values()):
            raise InvalidDraft('A link label is too long.')

    try:
        stored = (json.dumps(draft, ensure_ascii=False, sort_keys=True, separators=(',', ':')) + '\n').encode()
    except UnicodeError:
        raise InvalidDraft('Invalid Unicode in draft.') from None
    if len(stored) > MAX_BYTES:
        raise InvalidDraft('The draft exceeds 12 MB.')
    return stored
