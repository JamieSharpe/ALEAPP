from scripts.ilapfuncs import timeline, open_sqlite_db_readonly
from scripts.plugin_base import ArtefactPlugin
from scripts.artifact_report import ArtifactHtmlReport
from scripts.ilapfuncs import logfunc, tsv


class SMyFilesStoredPlugin(ArtefactPlugin):
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
        self.path_filters = ['**/com.sec.android.app.myfiles/databases/FileCache.db']  # Collection of regex search filters to locate an artefact.
        self.icon = ''  # feathricon for report.

    def _processor(self) -> bool:
    
        file_found = str(self.files_found[0])
        db = open_sqlite_db_readonly(file_found)
        cursor = db.cursor()
        cursor.execute('''
        SELECT
        datetime(date / 1000, "unixepoch"),
        storage,
        path,
        size,
        datetime(latest /1000, "unixepoch")
        from FileCache
        where path is not NULL 
        ''')

        all_rows = cursor.fetchall()
        usageentries = len(all_rows)
        if usageentries > 0:
            report = ArtifactHtmlReport('My Files DB - Stored Files')
            report.start_artifact_report(self.report_folder, 'My Files DB - Stored Files')
            report.add_script()
            data_headers = ('Timestamp','Storage','Path','Size','Latest' ) # Don't remove the comma, that is required to make this a tuple as there is only 1 element
            data_list = []
            for row in all_rows:
                data_list.append((row[0],row[1],row[2],row[3],row[4]))

            report.write_artifact_data_table(data_headers, data_list, file_found)
            report.end_artifact_report()

            tsvname = f'my files db - stored files'
            tsv(self.report_folder, data_headers, data_list, tsvname)

            tlactivity = f'My Files DB - Stored Files'
            timeline(self.report_folder, tlactivity, data_list, data_headers)
        else:
            logfunc('No My Files DB Stored data available')

        db.close()

        return True
