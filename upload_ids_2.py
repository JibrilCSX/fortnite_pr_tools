import time
from mwclient.errors import ProtectedPageError

from river_mwclient.esports_client import EsportsClient
from river_mwclient.auth_credentials import AuthCredentials
import csv
import mwparserfromhell

credentials = AuthCredentials(user_file="bot")
site = EsportsClient('fortnite-esports', credentials=credentials)
summary = 'Bot edit'

with open('SA_IDs.csv', 'r', encoding='utf-8') as f:
    id_reader = csv.reader(f)
    for row in id_reader:
        print(row)
        page = site.client.pages[row[1]]
        if not page.exists:
            continue
        text = page.text()
        wikitext = mwparserfromhell.parse(text)
        for template in wikitext.filter_templates():
            if template.name.matches('Infobox Player'):
                template.add('fortnite_id', row[0])
        new_text = str(wikitext)
        if text != new_text:
            time.sleep(1)
            print('Saving page %s....' % page.name)
            try:
                site.save(page, new_text, summary="Adding fortnite ID")
            except ProtectedPageError:
                continue
