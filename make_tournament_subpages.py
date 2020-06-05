from river_mwclient.auth_credentials import AuthCredentials
from river_mwclient.esports_client import EsportsClient
from re import search

pages_to_make = [
    {
        'match': 'Infobox Player',
        'pages': [
            {
                'pattern': '{}/Tournament Results',
                'text': '{{PlayerTabsHeader}}\n{{PlayerResults|show=everything}}',
            },
        ]
    },
]

summary = 'Automatically creating subpages/dependent pages'

credentials = AuthCredentials(user_file="bot")
site = EsportsClient('fortnite-esports', credentials=credentials)  # Set wiki

startat_page = 'Zamas'
passed_startat = False

for page in site.pages_using('Infobox Player'):
    if page.name == startat_page:
        passed_startat = True
    if not passed_startat:
        continue
    if page.namespace == 2:
        continue
    text = page.text()
    this_pages = None
    for page_set in pages_to_make:
        if page_set['match'] in text:
            this_pages = page_set['pages']
            break
    if this_pages is None:
        continue
    for item in this_pages:
        subpage = item['pattern'].format(page.name)
        if site.client.pages[subpage].exists:
            continue
        print('Saving page %s...' % page.name)
        site.client.pages[subpage].save(item['text'], summary=summary)
