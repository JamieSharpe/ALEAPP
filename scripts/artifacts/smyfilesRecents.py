from scripts.ilapfuncs import timeline, open_sqlite_db_readonly
from scripts.plugin_base import ArtefactPlugin
from scripts.artifact_report import ArtifactHtmlReport
from scripts.ilapfuncs import logfunc, tsv


class SMyFilesRecentsPlugin(ArtefactPlugin):
    """
    """

    def __init__(self):
        super().__init__()
        self.author = 'Unknown'
        self.author_email = ''
        self.author_url = ''

        self.name = 'Media Metadata'
        self.description = ''

        self.artefact_reference = ''  # Description on what the artefact is.
        self.path_filters = ['**/com.sec.android.app.myfiles/databases/myfiles.db']  # Collection of regex search filters to locate an artefact.
        self.icon = ''  # feathricon for report.

    def _processor(self) -> bool:
    
        file_found = str(self.files_found[0])
        db = open_sqlite_db_readonly(file_found)
        cursor = db.cursor()
        try:
            cursor.execute('''
            select
            datetime(date / 1000, "unixepoch"),
            name,
            size,
            _data,
            ext,
            _source,
            _description,
            datetime(recent_date / 1000, "unixepoch")
            from recent_files 
            ''')

            all_rows = cursor.fetchall()
            usageentries = len(all_rows)
        except:
            usageentries = 0

        if usageentries > 0:
            report = ArtifactHtmlReport('My Files DB - Recent Files')
            report.start_artifact_report(self.report_folder, 'My Files DB - Recent Files')
            report.add_script()
            data_headers = ('Timestamp','Name','Size','Data','Ext.', 'Source', 'Description', 'Recent Timestamp' )
            data_list = []
            for row in all_rows:
                data_list.append((row[0],row[1],row[2],row[3],row[4],row[5],row[6],row[7]))

            report.write_artifact_data_table(data_headers, data_list, file_found)
            report.end_artifact_report()

            tsvname = f'my files db - recent files'
            tsv(self.report_folder, data_headers, data_list, tsvname)

            tlactivity = f'My Files DB - Recent Files'
            timeline(self.report_folder, tlactivity, data_list, data_headers)
        else:
            logfunc('No My Files DB Recents data available')

        db.close()

        return True
