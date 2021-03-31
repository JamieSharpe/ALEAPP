from scripts.ilapfuncs import timeline, open_sqlite_db_readonly
from scripts.plugin_base import ArtefactPlugin
from scripts.artifact_report import ArtifactHtmlReport
from scripts.ilapfuncs import logfunc, tsv
from scripts import artifact_report

class EmulatedSMetaVideosPlugin(ArtefactPlugin):
    """
    """

    def __init__(self):
        super().__init__()
        self.author = 'Unknown'
        self.author_email = ''
        self.author_url = ''

        self.category = 'Emulated Storage Metadata'
        self.name = 'Videos'
        self.description = ''

        self.artefact_reference = ''  # Description on what the artefact is.
        self.path_filters = ['**/com.google.android.providers.media.module/databases/external.db*']  # Collection of regex search filters to locate an artefact.
        self.icon = ''  # feathricon for report.

        self.debug_mode = True

    def _processor(self) -> bool:

        for file_found in self.files_found:
            file_found = str(file_found)
            if not file_found.endswith('external.db'):
                continue # Skip all other files

            db = open_sqlite_db_readonly(file_found)
            cursor = db.cursor()

            cursor.execute('''
            SELECT
            datetime(date_added,  'unixepoch'),
            datetime(date_modified, 'unixepoch'),
            datetime(datetaken, 'unixepoch'),
            _display_name,
            _size,
            owner_package_name,
            bucket_display_name,
            relative_path,
            is_download,
            is_favorite,
            is_trashed
            from video
            ''')

            all_rows = cursor.fetchall()
            usageentries = len(all_rows)
            if usageentries > 0:

                data_headers = ('Key Timestamp','Date Added','Date Modified','Date Taken','Display Name','Size','Owner Package Name','Bucket Display Name','Relative Path','Is download?','Is favorite?','Is trashed?')
                data_list = []
                for row in all_rows:
                    if bool(row[0]):
                        keytime = row[0]
                    else:
                        keytime = row[1]
                    data_list.append((keytime, row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7], row[8], row[9], row[10]))

                artifact_report.GenerateHtmlReport(self, file_found, data_headers, data_list)

                tsv(self.report_folder, data_headers, data_list, self.name)

                timeline(self.report_folder, self.name, data_list, data_headers)
            else:
                logfunc('No Emulated Storage Metadata Videos data available')


            db.close()

        return True
