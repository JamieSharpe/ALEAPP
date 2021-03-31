from scripts.ilapfuncs import is_platform_windows, open_sqlite_db_readonly
from scripts.plugin_base import ArtefactPlugin
from scripts.artifact_report import ArtifactHtmlReport
from scripts.ilapfuncs import logfunc, tsv
from scripts import artifact_report


class AccountsCeAuthTokensPlugin(ArtefactPlugin):
    """
    """

    def __init__(self):
        super().__init__()
        self.author = 'Unknown'
        self.author_email = ''
        self.author_url = ''

        self.category = 'Accounts CE'
        self.name = 'Auth Tokens'
        self.description = ''

        self.artefact_reference = ''  # Description on what the artefact is.
        self.path_filters = ['**/accounts_ce.db']  # Collection of regex search filters to locate an artefact.
        self.icon = 'user'  # feathricon for report.

    def _processor(self) -> bool:

        slash = '\\' if is_platform_windows() else '/'

        # Filter for path xxx/yyy/system_ce/0
        for file_found in self.files_found:
            file_found = str(file_found)
            parts = file_found.split(slash)
            uid = parts[-2]
            try:
                uid_int = int(uid)
                # Skip sbin/.magisk/mirror/data/system_de/0 , it should be duplicate data??
                if file_found.find('{0}mirror{0}'.format(slash)) >= 0:
                    continue
                self._process_accounts_ce_authtokens(file_found, uid)
            except ValueError:
                    pass # uid was not a number

    def _process_accounts_ce_authtokens(self, folder, uid):

        #Query to create report
        db = open_sqlite_db_readonly(folder)
        cursor = db.cursor()

        #Query to create report
        cursor.execute('''
        SELECT
            accounts._id,
            accounts.name,
            accounts.type,
            authtokens.type,
            authtokens.authtoken
        FROM accounts, authtokens
        WHERE
            accounts._id = authtokens.accounts_id
        ''')
        all_rows = cursor.fetchall()
        usageentries = len(all_rows)
        if usageentries > 0:
            data_headers = ('ID', 'Name', 'Account Type','Authtoken Type', 'Authtoken')
            data_list = []
            for row in all_rows:
                data_list.append((row[0], row[1], row[2], row[3], row[4]))
            artifact_report.GenerateHtmlReport(self, f'{folder} - {uid}', data_headers, data_list)

            tsv(self.report_folder, data_headers, data_list, self.full_name())
        else:
            logfunc(f'No Authtokens_{uid} data available')
        db.close()
