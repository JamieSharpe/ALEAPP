from scripts.ilapfuncs import timeline, is_platform_windows, open_sqlite_db_readonly
from scripts.plugin_base import ArtefactPlugin
from scripts.artifact_report import ArtifactHtmlReport
from scripts.ilapfuncs import logfunc, tsv
from scripts import artifact_report

class AccountsDePlugin(ArtefactPlugin):
    """
    """

    def __init__(self):
        super().__init__()
        self.author = 'Unknown'
        self.author_email = ''
        self.author_url = ''

        self.name = 'Accounts_de'
        self.description = ''

        self.artefact_reference = ''  # Description on what the artefact is.
        self.path_filters = ['**/system_de/*/accounts_de.db']  # Collection of regex search filters to locate an artefact.
        self.icon = ''  # feathricon for report.

        self.debug_mode = True

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
                self._process_accounts_de(file_found, uid)
            except ValueError:
                    pass # uid was not a number

        return True

    def _process_accounts_de(self, folder, uid):

        #Query to create report
        db = open_sqlite_db_readonly(folder)
        cursor = db.cursor()

        #Query to create report
        cursor.execute('''
        SELECT
            datetime(last_password_entry_time_millis_epoch / 1000, 'unixepoch') as 'last pass entry',
            name,
            type
            FROM
        accounts
        ''')
        all_rows = cursor.fetchall()
        usageentries = len(all_rows)
        if usageentries > 0:
            data_headers = ('Last password entry','Name','Type')
            data_list = []
            for row in all_rows:
                data_list.append((row[0], row[1], row[2]))
            artifact_report.GenerateHtmlReport(self, f'{folder} - {uid}', data_headers, data_list)

            tsvname = f'accounts de {uid}'
            tsv(self.report_folder, data_headers, data_list, tsvname)

            tlactivity = f'Accounts DE {uid}'
            timeline(self.report_folder, tlactivity, data_list, data_headers)
        else:
            logfunc(f'No accounts_de_{uid} data available')
        db.close()
