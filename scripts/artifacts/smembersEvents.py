from scripts.ilapfuncs import timeline, open_sqlite_db_readonly
from scripts.plugin_base import ArtefactPlugin
from scripts.artifact_report import ArtifactHtmlReport
from scripts.ilapfuncs import logfunc, tsv
from scripts import artifact_report

class SMembersEventsPlugin(ArtefactPlugin):
    """
    """

    def __init__(self):
        super().__init__()
        self.author = 'Unknown'
        self.author_email = ''
        self.author_url = ''

        self.name = 'Samsung Members - Events'
        self.description = ''

        self.artefact_reference = ''  # Description on what the artefact is.
        self.path_filters = ['**/com.samsung.oh/databases/com_pocketgeek_sdk.db']  # Collection of regex search filters to locate an artefact.
        self.icon = ''  # feathricon for report.

        self.debug_mode = False

    def _processor(self) -> bool:

    
        file_found = str(self.files_found[0])
        db = open_sqlite_db_readonly(file_found)
        cursor = db.cursor()
        cursor.execute('''
        select 
        datetime(created_at /1000, "unixepoch"), 
        type, 
        value,
        in_snapshot
        FROM device_events
        ''')

        all_rows = cursor.fetchall()
        usageentries = len(all_rows)
        if usageentries > 0:

            data_headers = ('Created At','Type','Value','Snapshot?' )
            data_list = []
            for row in all_rows:
                data_list.append((row[0],row[1],row[2],row[3]))
            artifact_report.GenerateHtmlReport(self, file_found, data_headers, data_list)

            tsvname = f'samsung members - events'
            tsv(self.report_folder, data_headers, data_list, tsvname)

            tlactivity = f'Samsung Members - Events'
            timeline(self.report_folder, tlactivity, data_list, data_headers)
        else:
            logfunc('No Samsung Members - Events data available')

        db.close()

        return True
