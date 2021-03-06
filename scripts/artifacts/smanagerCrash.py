from scripts.ilapfuncs import timeline, open_sqlite_db_readonly
from scripts.plugin_base import ArtefactPlugin
from scripts.artifact_report import ArtifactHtmlReport
from scripts.ilapfuncs import logfunc, tsv
from scripts import artifact_report

class SManagerCrashPlugin(ArtefactPlugin):
    """
    """

    def __init__(self):
        super().__init__()
        self.author = 'Unknown'
        self.author_email = ''
        self.author_url = ''

        self.name = 'Samsung Smart Manager - Crash'
        self.description = ''

        self.artefact_reference = ''  # Description on what the artefact is.
        self.path_filters = ['*/com.samsung.android.sm/databases/sm.db']  # Collection of regex search filters to locate an artefact.
        self.icon = 'alert-triangle'  # feathricon for report.

    def _processor(self) -> bool:
    
        file_found = str(self.files_found[0])
        db = open_sqlite_db_readonly(file_found)
        cursor = db.cursor()
        cursor.execute('''
        SELECT
        datetime(crash_time / 1000, "unixepoch"),
        package_name
        from crash_info
        ''')

        all_rows = cursor.fetchall()
        usageentries = len(all_rows)
        if usageentries > 0:
            data_headers = ('Timestamp','Package Name')
            data_list = []
            for row in all_rows:
                data_list.append((row[0],row[1]))

            artifact_report.GenerateHtmlReport(self, file_found, data_headers, data_list)

            tsv(self.report_folder, data_headers, data_list, self.full_name())

            timeline(self.report_folder, self.name, data_list, data_headers)
        else:
            logfunc('No Samsung Smart Manager - Crash data available')

        db.close()

        return True
