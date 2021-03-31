from scripts.ilapfuncs import timeline, open_sqlite_db_readonly
from scripts.plugin_base import ArtefactPlugin
from scripts.artifact_report import ArtifactHtmlReport
from scripts.ilapfuncs import logfunc, tsv
from scripts import artifact_report

class SSmartManagerPlugin(ArtefactPlugin):
    """
    """

    def __init__(self):
        super().__init__()
        self.author = 'Unknown'
        self.author_email = ''
        self.author_url = ''

        self.name = 'Samsung Smart Manager - Usage'
        self.description = ''

        self.artefact_reference = ''  # Description on what the artefact is.
        self.path_filters = ['**/com.samsung.android.sm/databases/lowpowercontext-system-db']  # Collection of regex search filters to locate an artefact.
        self.icon = ''  # feathricon for report.

    def _processor(self) -> bool:
    
        file_found = str(self.files_found[0])
        db = open_sqlite_db_readonly(file_found)
        cursor = db.cursor()
        cursor.execute('''
        SELECT 
        datetime(start_time /1000, "unixepoch"),
        datetime(end_time /1000, "unixepoch"),
        id,
        package_name,
        uploaded,
        datetime(created_at /1000, "unixepoch"),
        datetime(modified_at /1000, "unixepoch")
        from usage_log
        ''')

        all_rows = cursor.fetchall()
        usageentries = len(all_rows)
        if usageentries > 0:
            data_headers = ('Start Time','End Time','ID','Package Name', 'Uploaded?', 'Created', 'Modified' )
            data_list = []
            for row in all_rows:
                data_list.append((row[0],row[1],row[2],row[3],row[4],row[5],row[6]))

            artifact_report.GenerateHtmlReport(self, file_found, data_headers, data_list)

            tsv(self.report_folder, data_headers, data_list, self.full_name())

            timeline(self.report_folder, self.name, data_list, data_headers)
        else:
            logfunc('No Samsung Smart Manager - Usage data available')

        db.close()

        return True
