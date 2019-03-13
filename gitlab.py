# encoding: utf-8

import sys
import argparse
from workflow import Workflow, ICON_WEB, ICON_WARNING, web, PasswordNotFound

__VERSION__ = '0.1.0'

def get_repos(url, apikey):
    url = url + '/api/v4/projects'
    request_headers = {"Private-Token": apikey }
    request_params = dict(per_page=100, membership=True, archived=False)
    r = web.get(url, params=request_params, headers=request_headers)
    r.raise_for_status()

    results = r.json()
    repos = []
    for result in results:
        if not result['archived']:
            repos.append(result)

    return repos

def search_key(repo):
    elements = []
    elements.append(repo['name'])
    elements.append(repo['description'])

    return u' '.join(elements)

def main(wf):
    parser = argparse.ArgumentParser();
    parser.add_argument( '--setkey', dest='api_key', nargs='?', default=None)
    parser.add_argument( '--seturl', dest='url', nargs='?', default=None)
    parser.add_argument( '--query', dest='query', nargs='?', default=None)

    args = parser.parse_args(wf.args)

    if wf.update_available:
        wf.add_item('New version available',
            'Action this item to install the update',
            autocomplete='workflow:update',
            icon=ICON_INFO)

    if args.url:
        wf.settings['gitlab_url'] = args.url;
        return 0;

    url = wf.settings.get('gitlab_url', None)
    if not url:
        wf.add_item('No URL set', 'Please use gitlab seturl to set your instance url.', valid=False, icon=ICON_WARNING)
        wf.send_feedback()
        return 0

    # Check for api key
    if args.api_key:
        wf.save_password( 'gitlab_apikey', args.api_key)
        return 0 #success


    try:
        apikey = wf.get_password( 'gitlab_apikey', None)
    except PasswordNotFound:
        wf.add_item('No API key set', 'Please use gitlab setkey to set your API key.', valid=False, icon=ICON_WARNING)
        wf.send_feedback();
        return 0

    def wrapper():
        return get_repos(url, apikey)

    repos = wf.cached_data('repos', wrapper, max_age=600)

    query = args.query
    if query:
        repos = wf.filter(query, repos, key=search_key, min_score=20)

    for repo in repos:
        wf.add_item(title=repo['name_with_namespace'], subtitle=repo['web_url'], arg=repo['web_url'], valid=True)

    wf.send_feedback()
    return 0

if __name__ == u"__main__":
    wf = Workflow(update_settings={
        'github_slug': 'ninnypants/gitlab-workflow',
        'version': __VERSION__,
        })
    wf.run(main)
