from river_mwclient.esports_client import EsportsClient
from river_mwclient.auth_credentials import AuthCredentials
import mwparserfromhell, time

limit = -1
quiet = True

credentials = AuthCredentials(user_file="me")
site = EsportsClient('fortnite', credentials=credentials)  # set wiki
summary = 'Automatically create player pages for Power Rankings'
summary2 = 'Automatically changing infobox name after moving page'

# RosterIds and RosterLinks should obviously be its own table
# but the table schema sucks and I don't want to redesign the entire thing
# so we'll get one row for each player that doesn't exist but then we'll still
# have to look up in the full list of links and ids
# to figure out which id this corresponds to
# both RosterLinks and RosterIds are List-of-typed fields
# but the proper schema for this would obviously be to have a separate table TournamentPlayers
# and just have Player & ID and none of this
# list-type fields were a mistake

result = site.cargo_client.query(
    tables='TournamentResults=TR,TournamentResults__RosterLinks=RL,_pageData=PD,Tournaments=T',
    join_on='TR._ID=RL._rowID,RL._value=PD._pageName,TR.OverviewPage=T._pageName',
    where='PD._pageName IS NULL AND RL._value IS NOT NULL AND TR.PRPoints > "0"',
    fields='TR._pageName=tournament,RL._value=name,T.Region=res, TR.RosterLinks__full=RosterLinks, TR.RosterIds__full=RosterIds',
    group_by='RL._value',
    limit='max'
)
if not quiet:
    print(result)
default_text = site.client.pages['Help:Player Template'].text()
default_text = default_text.replace('<noinclude>', '').replace('</noinclude>', '').strip()

wikitext = mwparserfromhell.parse(default_text)
this_template = None
for template in wikitext.filter_templates():
    if template.name.matches('Infobox Player'):
        this_template = template
        this_template.add('pronly', 'Yes')
        break

lmt = 0
for item in result:
    print(item)
    if lmt == limit:
        break
    lmt = lmt + 1
    name = item['name']
    if not quiet:
        print(name)
        print(item)
    res = item['res']
    idx = None
    item['RosterLinks'] = item['RosterLinks'].split(';;')
    item['RosterIds'] = item['RosterIds'].split(';;')
    for i, namex in enumerate(item['RosterLinks']):
        if namex.strip() == name:
            idx = item['RosterIds'][i]
            break
    if name == '0':
        continue
    try:
        if "&quot;" in name:
            if not quiet:
                print('Illegal character in Name %s, skipping' % name)
            continue
        page = site.client.pages[name]
        if page.text() != '':
            if not quiet:
                print('Page %s already exists, skipping' % name)
            site.save(page, page.text())
            continue
        if not quiet:
            print('Processing page %s...' % name)

        # if we know the player id and they don't have a page yet
        if idx is not None:
            this_template.add('fortnite_id', idx)

            # see if they have a page under a different name
            original_page_name = site.cargo_client.query_one_result(
                tables="Players",
                fields="_pageName=\"Page\"",
                where='FortniteId="{}"'.format(idx)
            )

            # if so then move it to the new name (dw about fixing double redirects, whatever)
            if original_page_name is not None:
                site.client.pages[original_page_name].move(name)
                site.client.pages['tournament'].touch()
                site.client.pages[original_page_name].touch()
                this_wikitext = mwparserfromhell.parse(site.client.pages[name].text())
                for template in this_wikitext.filter_templates():
                    if template.name.matches('Infobox Player'):
                        template.add('id', name)
                        break
                site.client.pages[name].edit(str(this_wikitext), summary=summary2)
                site.client.pages[name].purge()
                continue

        this_template.add('residency', res)
        this_template.add('id', name)
        text = str(wikitext)
        site.save(page, text, summary=summary)
    except Exception as e:
        time.sleep(10)
        site.client.pages['User:RheingoldRiver/auto players errors'].append('\n' + str(e) + ', player: ' + name)
