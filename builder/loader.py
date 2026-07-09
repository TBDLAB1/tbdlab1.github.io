import certifi
import dateutil.parser
import re
import json
import urllib
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from . import config

SHEETS_URL_BASE = 'https://sheets.googleapis.com/v4/spreadsheets'
DRIVE_FILES_URL = 'https://www.googleapis.com/drive/v3/files'
# The Gallery tab maps an album (title + optional Markdown description) to a
# Google Drive folder; every image in that folder becomes a slide.
GALLERY_RANGE = 'Gallery!A2:C'
RANGES = [
    'Website!B2:C',
    'Announcements!A2:C',
    'Members!A2:H',
    'Research!A2:F',
    'Tags!A2:F',
    'Links!A2:G',
    'Pages!A2:C',
    'Redirects!A2:B',
    'Personal!A2:B',
]
PERSONAL_RANGES = [
    'Website!B2:C',
    'Contents!A2:B',
]
MENU_RANGE = 'Menu!A2:C'
# Used when the spreadsheet has no 'Menu' tab yet, so existing sites keep working.
DEFAULT_MENU = [
    {'title': 'Home', 'url': '/', 'children': []},
    {'title': 'Members', 'url': '/members', 'children': []},
    {'title': 'Research', 'url': '/research', 'children': []},
    {'title': 'Links', 'url': '/links', 'children': []},
    {'title': 'Contact', 'url': '/contact', 'children': []},
]
# Any spreadsheet tab named "Members - <Name>" becomes its own member page at
# /members/<slug-of-name>, managed independently from the main Members tab.
MEMBER_PAGE_PREFIX = 'Members - '

def get_doc_id(data_url):
    tokens = data_url.split('/')
    doc_id = ''
    # Use a heuristic method for finding document ID from the URL.
    for token in tokens:
        if re.match(r'[a-zA-Z0-9]+', token) is not None:
            if len(token) > len(doc_id):
                doc_id = token
    return doc_id

def get_drive_folder_id(link):
    link = (link or '').strip()
    if not link:
        return ''
    m = re.search(r'/folders/([a-zA-Z0-9_-]+)', link)
    if m:
        return m.group(1)
    # A bare id, or some other URL form: drop any query string and take the
    # longest path segment.
    link = link.split('?')[0]
    tokens = [t for t in link.split('/') if t]
    return max(tokens, key=len) if tokens else ''

def list_drive_images(folder_id):
    query = "'%s' in parents and mimeType contains 'image/' and trashed = false" % folder_id
    params = urllib.parse.urlencode({
        'q': query,
        'key': config.API_KEY,
        'fields': 'files(id,name)',
        'orderBy': 'name_natural',
        'pageSize': 100,
    })
    url = '%s?%s' % (DRIVE_FILES_URL, params)
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, cafile=certifi.where()) as response:
        data = response.read()
    files = json.loads(data).get('files', [])
    return [{
        'name': f.get('name', ''),
        'url': 'https://drive.google.com/thumbnail?id=%s&sz=w1600' % f['id'],
    } for f in files if f.get('id')]

def list_drive_subfolders(folder_id):
    query = "'%s' in parents and mimeType = 'application/vnd.google-apps.folder' and trashed = false" % folder_id
    params = urllib.parse.urlencode({
        'q': query,
        'key': config.API_KEY,
        'fields': 'files(id,name)',
        'pageSize': 100,
    })
    url = '%s?%s' % (DRIVE_FILES_URL, params)
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, cafile=certifi.where()) as response:
        data = response.read()
    files = json.loads(data).get('files', [])
    return {f['name']: f['id'] for f in files if f.get('id') and f.get('name')}

def load_ranges(doc_id, ranges):
    if not config.API_KEY:
        raise RuntimeError('API_KEY is empty. Set the API_KEY secret (repo Settings -> Secrets and variables -> Actions).')
    if not doc_id:
        raise RuntimeError('DATA_URL is empty or has no document id. Set the DATA_URL secret to your Google Sheets URL.')
    params = '&'.join(['ranges=%s' % urllib.parse.quote(r) for r in ranges])
    url = '%s/%s/values:batchGet?%s&key=%s' % (SHEETS_URL_BASE, doc_id, params, config.API_KEY)

    req = urllib.request.Request(url)
    try:
        with urllib.request.urlopen(req, cafile=certifi.where()) as response:
            data = response.read()
    except urllib.error.HTTPError as e:
        # urllib hides the response body; print Google's actual error reason
        # (e.g. API_KEY_HTTP_REFERRER_BLOCKED, SERVICE_DISABLED, API_KEY_INVALID).
        body = e.read().decode('utf-8', 'replace')
        print('Google Sheets API returned HTTP %s. Response body:\n%s' % (e.code, body))
        raise
    data_dict = json.loads(data)
    # A range with no data omits the 'values' key, so default to an empty list.
    return [r.get('values', []) for r in data_dict['valueRanges']]

def row_to_dict(row, keys, start_at=0):
    i = start_at
    result_dict = {}
    for key in keys:
        if len(row) > i:
            result_dict[key] = row[i]
        else:
            result_dict[key] = ''
        i += 1
    return result_dict

def is_empty_row(row):
    # Google Sheets omits trailing empty cells, so a row may be short or empty.
    # Treat a row with no value in its first column as a blank/junk row.
    return not row or not str(row[0]).strip()

def conv_website(table):
    items = {}
    for row in table:
        if is_empty_row(row):
            continue
        items[row[0]] = row[1] if len(row) > 1 else ''
    return items

def conv_announcements(table):
    items = []
    for row in table:
        if is_empty_row(row):
            continue
        if len(row) > 2 and row[2]:
            expire_at = dateutil.parser.parse(row[2])
            now = datetime.now(timezone.utc)
            if expire_at <= now:
                # This is already expired.
                continue
        items.append({
            'title': row[0],
            'content': row[1] if len(row) > 1 else ''
        })
    return items

def conv_members(table):
    groups = []
    group = None
    for row in table:
        if is_empty_row(row):
            continue
        title = row[0]
        if group is None or group['title'] != title:
            if group:
                groups.append(group)
            group = {'title': title, 'members': []}
        member = row_to_dict(row, ['name', 'email', 'image', 'description', 'links', 'degree', 'year'], 1)
        group['members'].append(member)
    if group:
        groups.append(group)
    return groups

def conv_research(table):
    groups = []
    group = None
    for row in table:
        if is_empty_row(row):
            continue
        title = row[0]
        if group is None or group['title'] != title:
            if group:
                groups.append(group)
            group = {'title': title, 'rows': []}
        item = row_to_dict(row, ['title', 'authors', 'booktitle', 'links', 'tags'], 1)
        if 'tags' in item:
            item['tags'] = [tag.strip() for tag in (item['tags'] or '').split(',') if tag]
        group['rows'].append(item)
    if group:
        groups.append(group)
    return groups

def conv_tags(table):
    tags = {}
    for row in table:
        if is_empty_row(row):
            continue
        tags[row[0]] = {
            'title': row[1] if len(row) > 1 else '',
            'tag': row[2] if len(row) > 2 else '',
            'color': row[3] if len(row) > 3 else '',
        }
    return tags

def conv_links(table):
    groups = []
    group = None
    for row in table:
        if is_empty_row(row):
            continue
        title = row[0]
        if group is None or group['title'] != title:
            if group:
                groups.append(group)
            group = {'title': title, 'rows': []}
        item = row_to_dict(row, ['title', 'full_title', 'url', 'query', 'call_month', 'event_month'], 1)
        group['rows'].append(item)
    if group:
        groups.append(group)
    return groups

def conv_personal_website(table):
    items = {}
    for row in table:
        if not row or not row[0].strip():
            continue
        items[row[0]] = row[1] if len(row) > 1 else ''
    return items

def conv_personal_contents(table):
    contents = []
    for row in table:
        if len(row) < 2 or not row[0].strip():
            continue
        contents.append({'title': row[0], 'content': row[1]})
    return contents

def load_personal(table):
    websites = []
    for row in table:
        pathname = row[0].strip()
        url = row[1].strip()
        if not pathname or not url:
            continue
        websites.append({'path': pathname, 'url': url})
    
    websites_returned = list()
    for website in websites:
        data_url = website['url']
        doc_id = get_doc_id(data_url)
        try:
            tables = load_ranges(doc_id, PERSONAL_RANGES)
        except urllib.error.HTTPError:
            print("Error: {}".format(website))
            continue
        website['website'] = conv_personal_website(tables[0])
        website['contents'] = conv_personal_contents(tables[1])
        websites_returned.append(website)

    return websites_returned

def conv_pages(table):
    pages = []
    for row in table:
        if len(row) < 3 or not row[0].strip():
            continue
        pathname = row[0].strip()
        title = row[1].strip()
        content = row[2]
        if not pathname or not title or not content:
            continue
        pages.append({'path': pathname, 'title': title, 'content': content})
    return pages

def conv_redirects(table):
    redirects = []
    for row in table:
        if len(row) < 2 or not row[0].strip():
            continue
        pathname = row[0].strip()
        url = row[1].strip()
        if not pathname or not url:
            continue
        redirects.append({'path': pathname, 'url': url})
    return redirects

def conv_menu(table):
    # Group rows by the first column (top-level label), following the same
    # pattern as members/research/links. A row with an empty second column
    # sets the top-level item's own link; rows with a second column become
    # submenu items, which turns the top-level item into a dropdown.
    groups = []
    group = None
    for row in table:
        if is_empty_row(row):
            continue
        title = row[0].strip()
        sub = row[1].strip() if len(row) > 1 else ''
        url = row[2].strip() if len(row) > 2 else ''
        if group is None or group['title'] != title:
            if group:
                groups.append(group)
            group = {'title': title, 'url': '', 'children': []}
        if sub:
            group['children'].append({'title': sub, 'url': url})
        else:
            group['url'] = url
    if group:
        groups.append(group)
    return groups

def load_menu(doc_id):
    try:
        tables = load_ranges(doc_id, [MENU_RANGE])
    except urllib.error.HTTPError:
        # No 'Menu' tab in the spreadsheet yet.
        return DEFAULT_MENU
    menu = conv_menu(tables[0]) if tables else []
    return menu or DEFAULT_MENU

def slugify(text):
    text = (text or '').strip().lower()
    text = re.sub(r'[^a-z0-9]+', '-', text)
    return text.strip('-')

def get_sheet_titles(doc_id):
    url = '%s/%s?fields=sheets.properties.title&key=%s' % (SHEETS_URL_BASE, doc_id, config.API_KEY)
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, cafile=certifi.where()) as response:
        data = response.read()
    data_dict = json.loads(data)
    return [s['properties']['title'] for s in data_dict.get('sheets', [])]

def load_member_pages(doc_id):
    pages = []
    try:
        titles = get_sheet_titles(doc_id)
    except urllib.error.HTTPError:
        return pages
    for title in titles:
        if not title.startswith(MEMBER_PAGE_PREFIX):
            continue
        name = title[len(MEMBER_PAGE_PREFIX):].strip()
        slug = slugify(name)
        if not name or not slug:
            continue
        try:
            tables = load_ranges(doc_id, ["'%s'!A2:H" % title])
        except urllib.error.HTTPError:
            print('Error: unable to load member page tab "%s"' % title)
            continue
        pages.append({
            'slug': slug,
            'title': name,
            'members': conv_members(tables[0]) if tables else [],
        })
    return pages

def load_gallery(doc_id, root_folder_link=''):
    try:
        tables = load_ranges(doc_id, [GALLERY_RANGE])
    except urllib.error.HTTPError:
        # No 'Gallery' tab in the spreadsheet yet.
        return []
    rows = tables[0] if tables else []

    # Album folders are named subfolders inside the root gallery folder
    # (Website tab 'gallery_folder'), so a row only needs the subfolder name.
    subfolders = {}
    root_id = get_drive_folder_id(root_folder_link)
    if root_id:
        try:
            subfolders = list_drive_subfolders(root_id)
        except urllib.error.HTTPError:
            print('Error: cannot list the gallery root folder')

    albums = []
    for row in rows:
        if is_empty_row(row):
            continue
        title = row[0].strip()
        ref = (row[1] if len(row) > 1 else '').strip()
        # Allow a literal "\n" typed in the cell to act as a line break, in
        # addition to real line breaks (Alt+Enter).
        content = (row[2] if len(row) > 2 else '').replace('\\n', '\n')
        # A full Drive link is used as-is; otherwise treat the value as the
        # name of a subfolder inside the root gallery folder.
        if '/folders/' in ref or 'drive.google' in ref:
            folder_id = get_drive_folder_id(ref)
        else:
            folder_id = subfolders.get(ref, '')
        photos = []
        if folder_id:
            try:
                photos = list_drive_images(folder_id)
            except urllib.error.HTTPError:
                print('Error: cannot list Drive folder for gallery album "%s"' % title)
        elif ref:
            print('Warning: gallery album "%s": folder "%s" not found in root' % (title, ref))
        albums.append({'title': title, 'content': content, 'photos': photos})
    return albums

def load_data():
    data_url = config.DATA_URL
    doc_id = get_doc_id(data_url)
    tables = load_ranges(doc_id, RANGES)
    website = conv_website(tables[0])
    return {
        'website': website,
        'announcements': conv_announcements(tables[1]),
        'members': conv_members(tables[2]),
        'research': conv_research(tables[3]),
        'tags': conv_tags(tables[4]),
        'links': conv_links(tables[5]),
        'pages': conv_pages(tables[6]),
        'redirects': conv_redirects(tables[7]),
        'personal': load_personal(tables[8]),
        'menu': load_menu(doc_id),
        'member_pages': load_member_pages(doc_id),
        'gallery': load_gallery(doc_id, website.get('gallery_folder', '')),
    }

