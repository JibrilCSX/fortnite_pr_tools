from river_mwclient.esports_client import EsportsClient
from river_mwclient.auth_credentials import AuthCredentials
import mwparserfromhell
from mwclient.page import Page
from mwclient.errors import EditError


class PointUpdater(object):
    SUMMARY = 'Automatic Squad Update'  # Set summary
    PLAYERS_PER_SQUAD = 4
    CURRENT_YEAR = 2021
    CURRENT_YEAR_STR = str(CURRENT_YEAR)

    def __init__(self, site: EsportsClient):
        self.site = site

    def run(self):
        pages = self.get_pages()
        for page in pages:
            lookup = self.get_player_squads(page)
            self.update_and_save(page, lookup)

    def get_pages(self):
        this_template = self.site.client.pages['Template:Listplayer/Current']  # Set template
        return this_template.embeddedin(namespace=0)

    def get_player_squads(self, page: Page):
        # we will assume that LPC name exactly matches player page name
        # otherwise we need an extra copy of PR and ew
        table_list = [
            "Teams",
            "ListplayerCurrent=LPC",
            "PlayerRedirects=PR",
            "TournamentResults__RosterLinks=RL",
            "TournamentResults=Res",
            "Tournaments=T"
        ]
        join_list = [
            "Teams._pageName=LPC._pageName",
            "LPC.Link=PR._pageName",
            "PR.AllName=RL._value",
            "RL._rowID=Res._ID",
            "Res.OverviewPage=T._pageName",
        ]
        where = [
            'LPC._pageName="%s"' % page.name,
            '(T.Date >= "{}-01-01" AND T.Date <= "{}-12-31")'.format(
                self.CURRENT_YEAR_STR, self.CURRENT_YEAR_STR
            ),
            "Teams.Region=T.Region",
        ]
        pr_platform = self.get_prplatform(page)
        if pr_platform is not None:
            where.append('T.Platform LIKE "%{}%"'.format(pr_platform))

        # print(','.join(table_list))
        # print(','.join(join_list))
        # print(' AND '.join(['(%s)' % _ for _ in where]))
        # print(page.name)

        result = self.site.cargo_client.query(
            tables=','.join(table_list),
            join_on=','.join(join_list),
            group_by='PR._pageName',
            fields='LPC.Link=Link, SUM(Res.PRPoints)=Points',
            where=' AND '.join(['(%s)' % _ for _ in where]),
            order_by='SUM(Res.PRPoints) DESC'
        )
        lookup_table = {}
        # we can assume this is sorted bc of the order_by
        squad = 1
        counter = 0
        for line in result:
            if counter == self.PLAYERS_PER_SQUAD:
                squad += 1
                counter = 0
            lookup_table[line['Link']] = squad
            counter += 1
        return lookup_table

    @staticmethod
    def get_prplatform(page: Page):
        for template in mwparserfromhell.parse(page.text()).filter_templates():
            if not template.name.matches('Infobox Team'):
                continue
            if not template.has('prplatform'):
                return None
            return template.get('prplatform').value.strip()

    def update_and_save(self, page, lookup):
        text = page.text()
        wikitext = mwparserfromhell.parse(text)
        for template in wikitext.filter_templates():
            if template.name.matches(['Listplayer/Current']):
                player = template.get('1').value.strip()
                if player not in lookup:
                    template.add('squad', '')
                    continue
                template.add('squad', lookup[player])

        newtext = str(wikitext)
        if text != newtext:
            # print('Saving page %s...' % page.name)
            try:
                self.site.save(page, newtext, summary=self.SUMMARY)
            except EditError:
                self.site.log_error_content(page.name, 'Spam filter prohibited squad point update')
        else:
            pass
        # print('Skipping page %s...' % page.name)


if __name__ == '__main__':
    credentials = AuthCredentials(user_file="me")
    fn_site = EsportsClient('fortnite', credentials=credentials)  # set wiki
    point_updater = PointUpdater(fn_site)
    point_updater.run()
