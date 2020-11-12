import time
from mwclient.errors import ProtectedPageError

from river_mwclient.esports_client import EsportsClient
from river_mwclient.auth_credentials import AuthCredentials
import csv
import mwparserfromhell

credentials = AuthCredentials(user_file="bot")
site = EsportsClient('fortnite-esports', credentials=credentials)

for page in site.pages_using('Infobox Tournament'):
    text = page.text()
    if 'Tabs}}' not in text:
        text = '{{EmptyTournamentTabs}}\n' + text
        site.save(page, text, summary="Adding EmptyTournamentTabs")
