from river_mwclient.esports_client import EsportsClient
from river_mwclient.auth_credentials import AuthCredentials
from river_mwclient.template_modifier import TemplateModifierBase
from mwparserfromhell.nodes import Template

credentials = AuthCredentials(user_file="bot")
site = EsportsClient('fortnite-esports', credentials=credentials)
summary = 'Remove wrong fortnite ids'


class TemplateModifier(TemplateModifierBase):
    def update_template(self, template: Template):
        template.remove('fortnite_id')


page_list = site.cargo_client.page_list(tables="Players", where='FortniteID LIKE "%;%"', fields="OverviewPage", limit='max')

TemplateModifier(site, 'Infobox Player', page_list=page_list,
                 summary=summary).run()
