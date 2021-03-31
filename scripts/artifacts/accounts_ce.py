from scripts.ilapfuncs import is_platform_windows, open_sqlite_db_readonly
from scripts.plugin_base import ArtefactPlugin
from scripts.artifact_report import ArtifactHtmlReport
from scripts.ilapfuncs import logfunc, tsv
from scripts import artifact_report

class AccountsCePlugin(ArtefactPlugin):
    """
    """

    def __init__(self):
        super().__init__()
        self.author = 'Unknown'
        self.author_email = ''
        self.author_url = ''

        self.name = 'Accounts_ce'
        self.description = ''

        self.artefact_reference = ''  # Description on what the artefact is.
        self.path_filters = ['**/system_ce/*/accounts_ce.db']  # Collection of regex search filters to locate an artefact.
        self.icon = ''  # feathricon for report.

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
                self._process_accounts_ce(file_found, uid)
            except ValueError:
                    pass # uid was not a number

        return True

    def _process_accounts_ce(self, folder, uid):

        #Query to create report
        db = open_sqlite_db_readonly(folder)
        cursor = db.cursor()

        #Query to create report
        cursor.execute('''
        SELECT
            name,
            type,
            password
        FROM
        accounts
        ''')
        all_rows = cursor.fetchall()
        usageentries = len(all_rows)
        if usageentries > 0:
            data_headers = ('Name', 'Type', 'Password')
            data_list = []
            for row in all_rows:
                data_list.append((row[0], row[1], row[2]))
            artifact_report.GenerateHtmlReport(self, f'{folder} - {uid}', data_headers, data_list)

            tsvname = f'accounts ce {uid}'
            tsv(self.report_folder, data_headers, data_list, tsvname)
        else:
            logfunc(f'No accounts_ce_{uid} data available')
        db.close()
