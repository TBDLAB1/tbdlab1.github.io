from .renderer import *

class Page:
    def __init__(self, path, renderer):
        self.path = path
        self.renderer = renderer

def get_safe_path(pathname):
    if pathname.endswith('.html'):
        return pathname
    else:
        return '%s/index.html' % pathname

def lambda_render_page_lists(x, y, func):
    return lambda xx: func(xx, y)
    
def get_pages(data):
    return [
        Page('index.html', render_index),
        Page('members.html', render_members),
        Page('research.html', render_research),
        Page('links.html', render_links),
        Page('contact.html', render_contact),
        Page('gallery.html', render_gallery),
    ] + [
        Page(
            'members/%s.html' % member_page['slug'],
            lambda_render_page_lists(data, member_page, func=render_member_page)
        ) for member_page in data['member_pages']
    ] + [
        Page(
            get_safe_path(page['path']),
            lambda_render_page_lists(data, page, func=render_page)
        ) for page in data['pages']
    ] + [
        Page(
            get_safe_path(redirect['path']), 
            lambda_render_page_lists(data, redirect, func=render_redirect)
        ) for redirect in data['redirects']
    ] + [
        Page(
            get_safe_path(website_personal['path']), 
            lambda_render_page_lists(data, website_personal, func=render_personal_website),
        ) for website_personal in data['personal']
    ]
