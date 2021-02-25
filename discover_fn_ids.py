import mwparserfromhell
from river_mwclient.esports_client import EsportsClient
from river_mwclient.auth_credentials import AuthCredentials

limit = -1
quiet = True

credentials = AuthCredentials(user_file="bot")
site = EsportsClient('fortnite-esports', credentials=credentials)
summary = 'Discovering Fortnite IDs from tournament data'

result = site.cargo_client.query(
    tables='TournamentResults=TR,TournamentResults__RosterLinks=RL,_pageData=PD,Players=P',
    join_on='TR._ID=RL._rowID,RL._value=PD._pageName,RL._value=P.ID',
    where='PD._pageName IS NOT NULL AND TR.RosterIds__full NOT LIKE CONCAT("%", P.FortniteID, "%") AND TR.RosterLinks__full != TR.RosterIds__full',
    fields='RL._value=name, TR.RosterLinks__full=RosterLinks, TR.RosterIds__full=RosterIds',
    group_by='RL._value',
    limit='max'
)
print(result)
lmt = 0
for item in result:
    if lmt == limit:
        lmt = lmt + 1
    name = item['name']
    if not quiet:
        print(name)
        print(item)
    idx = None
    item['RosterLinks'] = item['RosterLinks'].split(';;')
    item['RosterIds'] = item['RosterIds'].split(';;')
    for i, namex in enumerate(item['RosterLinks']):
        if namex.strip() == name:
            idx = item['RosterIds'][i]
            break
    if idx is None or len(idx) != 32 or idx == name:  # Checks if the id is 32 character long
        continue
    try:
        int(idx, 16)  # Checks if the id is hexadecimal
    except ValueError:
        continue
    page = site.client.pages[name]
    if site.target(page) != name:
        page = site.client.pages[site.target(page)]
    text = page.text()
    wikitext = mwparserfromhell.parse(text)
    for template in wikitext.filter_templates():
        if template.name.matches("Infobox Player"):
            if template.has("fortnite_id"):
                if not quiet:
                    print("Skipped player %s. Might be a missing disambig." % name)
                # Skips if the player already has a Fortnite ID
                # if so, it might be a different player and has to be handled manually
                # https://fortnite-esports.gamepedia.com/Maintenance:Players_With_Multiple_Fortnite_IDs
                continue
            template.add("fortnite_id", idx)
            break
    if str(wikitext) == text:
        continue
    site.save_title(page.name, str(wikitext), summary=summary)
