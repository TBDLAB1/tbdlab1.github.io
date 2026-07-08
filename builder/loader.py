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

def get_doc_id(data_url):
    tokens = data_url.split('/')
    doc_id = ''
    # Use a heuristic method for finding document ID from the URL.
    for token in tokens:
        if re.match(r'[a-zA-Z0-9]+', token) is not None:
            if len(token) > len(doc_id):
                doc_id = token
    return doc_id

def load_ranges(doc_id, ranges):
    params = '&'.join(['ranges=%s' % urllib.parse.quote(r) for r in ranges])
    url = '%s/%s/values:batchGet?%s&key=%s' % (SHEETS_URL_BASE, doc_id, params, config.API_KEY)

    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, cafile=certifi.where()) as response:
        data = response.read()
    data_dict = json.loads(data)
    return [r['values'] for r in data_dict['valueRanges']]

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

def load_data():
    data_url = config.DATA_URL
    doc_id = get_doc_id(data_url)
    tables = load_ranges(doc_id, RANGES)
    return {
        'website': conv_website(tables[0]),
        'announcements': conv_announcements(tables[1]),
        'members': conv_members(tables[2]),
        'research': conv_research(tables[3]),
        'tags': conv_tags(tables[4]),
        'links': conv_links(tables[5]),
        'pages': conv_pages(tables[6]),
        'redirects': conv_redirects(tables[7]),
        'personal': load_personal(tables[8]),
    }

