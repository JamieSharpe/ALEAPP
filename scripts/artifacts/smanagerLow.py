from scripts.ilapfuncs import timeline, open_sqlite_db_readonly
from scripts.plugin_base import ArtefactPlugin
from scripts.artifact_report import ArtifactHtmlReport
from scripts.ilapfuncs import logfunc, tsv


class SSmartManagerPlugin(ArtefactPlugin):
    """
    """

    def __init__(self):
        super().__init__()
        self.author = 'Unknown'
        self.author_email = ''
        self.author_url = ''

        self.name = 'App Interaction'
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
            report = ArtifactHtmlReport('Samsung Smart Manager - Usage')
            report.start_artifact_report(self.report_folder, 'Samsung Smart Manager - Usage')
            report.add_script()
            data_headers = ('Start Time','End Time','ID','Package Name', 'Uploaded?', 'Created', 'Modified' )
            data_list = []
            for row in all_rows:
                data_list.append((row[0],row[1],row[2],row[3],row[4],row[5],row[6]))

            report.write_artifact_data_table(data_headers, data_list, file_found)
            report.end_artifact_report()

            tsvname = f'samsung smart manager - usage'
            tsv(self.report_folder, data_headers, data_list, tsvname)

            tlactivity = f'Samsung Smart Manager - Usage'
            timeline(self.report_folder, tlactivity, data_list, data_headers)
        else:
            logfunc('No Samsung Smart Manager - Usage data available')

        db.close()

        return True
