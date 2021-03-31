from scripts.ilapfuncs import timeline, open_sqlite_db_readonly
from scripts.plugin_base import ArtefactPlugin
from scripts.artifact_report import ArtifactHtmlReport
from scripts.ilapfuncs import logfunc, tsv
from scripts import artifact_report

class InstalledAppsLibraryPlugin(ArtefactPlugin):
    """
    """

    def __init__(self):
        super().__init__()
        self.author = 'Unknown'
        self.author_email = ''
        self.author_url = ''

        self.name = 'Installed Apps - Library'
        self.description = ''

        self.artefact_reference = ''  # Description on what the artefact is.
        self.path_filters = ['**/com.android.vending/databases/library.db']  # Collection of regex search filters to locate an artefact.
        self.icon = ''  # feathricon for report.

        self.debug_mode = False

    def _processor(self) -> bool:

        file_found = str(self.files_found[0])
        db = open_sqlite_db_readonly(file_found)
        cursor = db.cursor()
        cursor.execute('''
        SELECT
            case
            when purchase_time = 0 THEN ''
            when purchase_time > 0 THEN datetime(purchase_time / 1000, "unixepoch")
            END as pt,
            account,
            doc_id
        FROM
        ownership  
        ''')

        all_rows = cursor.fetchall()
        usageentries = len(all_rows)
        if usageentries > 0:
            data_headers = ('Purchase Time', 'Account', 'Doc ID')
            data_list = []
            for row in all_rows:
                data_list.append((row[0], row[1], row[2]))

            artifact_report.GenerateHtmlReport(self, file_found, data_headers, data_list)

            tsv(self.report_folder, data_headers, data_list, self.name)

            timeline(self.report_folder, self.name, data_list, data_headers)
        else:
            logfunc('No Installed Apps (Library) data available')

        db.close()
        return True
