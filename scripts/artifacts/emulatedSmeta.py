from scripts.ilapfuncs import timeline, open_sqlite_db_readonly
from scripts.plugin_base import ArtefactPlugin
from scripts.artifact_report import ArtifactHtmlReport
from scripts.ilapfuncs import logfunc, tsv


class EmulatedSMetaPlugin(ArtefactPlugin):
    """
    """

    def __init__(self):
        super().__init__()
        self.author = 'Unknown'
        self.author_email = ''
        self.author_url = ''

        self.name = 'Emulated Storage Metadata'
        self.description = ''

        self.artefact_reference = ''  # Description on what the artefact is.
        self.path_filters = ['**/com.google.android.providers.media.module/databases/external.db*']  # Collection of regex search filters to locate an artefact.
        self.icon = ''  # feathricon for report.

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
                referer_uri,
                download_uri,
                relative_path,
                is_download,
                is_favorite,
                is_trashed,
                xmp
            FROM downloads
            ''')

            all_rows = cursor.fetchall()
            usageentries = len(all_rows)
            if usageentries > 0:
                report = ArtifactHtmlReport('Downloads - Emulated Storage Metadata')
                report.start_artifact_report(self.report_folder, 'Downloads')
                report.add_script()
                data_headers = ('Key Timestamp','Date Added','Date Modified','Date Taken','Display Name','Size','Owner Package Name','Bucket Display Name','Referer URI','Download URI','Relative Path','Is download?','Is favorite?','Is trashed?','XMP')
                data_list = []
                for row in all_rows:
                    if bool(row[0]):
                        keytime = row[0]
                    else:
                        keytime = row[1]

                    if isinstance(row[13], bytes):
                        xmp = str(row[13])[2:-1]
                    else:
                        xmp = row[13]

                    data_list.append((keytime, row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7], row[8], row[9], row[10], row[11], row[12],xmp))

                report.write_artifact_data_table(data_headers, data_list, file_found)
                report.end_artifact_report()

                tsvname = f'Emulated Storage Metadata - Downloads'
                tsv(self.report_folder, data_headers, data_list, tsvname)

                tlactivity = f'Emulated Storage Metadata - Downloads'
                timeline(self.report_folder, tlactivity, data_list, data_headers)
            else:
                logfunc('No Emulated Storage Metadata Downloads data available')

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
            from images
            ''')

            all_rows = cursor.fetchall()
            usageentries = len(all_rows)
            if usageentries > 0:
                report = ArtifactHtmlReport('Images - Emulated Storage Metadata')
                report.start_artifact_report(self.report_folder, 'Images')
                report.add_script()
                data_headers = ('Key Timestamp','Date Added','Date Modified','Date Taken','Display Name','Size','Owner Package Name','Bucket Display Name','Relative Path','Is download?','Is favorite?','Is trashed?')
                data_list = []
                for row in all_rows:
                    if bool(row[0]):
                        keytime = row[0]
                    else:
                        keytime = row[1]
                    data_list.append((keytime, row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7], row[8], row[9], row[10]))




                report.write_artifact_data_table(data_headers, data_list, file_found)
                report.end_artifact_report()

                tsvname = f'Emulated Storage Metadata - Images'
                tsv(self.report_folder, data_headers, data_list, tsvname)

                tlactivity = f'Emulated Storage Metadata - Images'
                timeline(self.report_folder, tlactivity, data_list, data_headers)
            else:
                logfunc('No Emulated Storage Metadata Images data available')


            cursor.execute('''
            SELECT
            datetime(date_added,  'unixepoch'),
            datetime(date_modified, 'unixepoch'),
            datetime(datetaken, 'unixepoch'),
            _display_name,
            _size,
            owner_package_name,
            bucket_display_name,
            referer_uri,
            download_uri,
            relative_path,
            is_download,
            is_favorite,
            is_trashed
            from files
            ''')

            all_rows = cursor.fetchall()
            usageentries = len(all_rows)
            if usageentries > 0:
                report = ArtifactHtmlReport('Files - Emulated Storage Metadata')
                report.start_artifact_report(self.report_folder, 'Files')
                report.add_script()
                data_headers = ('Key Timestamp','Date Added','Date Modified','Date Taken','Display Name','Size','Owner Package Name','Bucket Display Name','Referer URI','Download URI','Relative Path','Is download?','Is favorite?','Is trashed?')
                data_list = []
                for row in all_rows:
                    if bool(row[0]):
                        keytime = row[0]
                    else:
                        keytime = row[1]
                    data_list.append((keytime, row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7], row[8], row[9], row[10], row[11], row[12]))

                report.write_artifact_data_table(data_headers, data_list, file_found)
                report.end_artifact_report()

                tsvname = f'Emulated Storage Metadata - Files'
                tsv(self.report_folder, data_headers, data_list, tsvname)

                tlactivity = f'Emulated Storage Metadata - Files'
                timeline(self.report_folder, tlactivity, data_list, data_headers)
            else:
                logfunc('No Emulated Storage Metadata Files data available')

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
                report = ArtifactHtmlReport('Videos - Emulated Storage Metadata')
                report.start_artifact_report(self.report_folder, 'Videos')
                report.add_script()
                data_headers = ('Key Timestamp','Date Added','Date Modified','Date Taken','Display Name','Size','Owner Package Name','Bucket Display Name','Relative Path','Is download?','Is favorite?','Is trashed?')
                data_list = []
                for row in all_rows:
                    if bool(row[0]):
                        keytime = row[0]
                    else:
                        keytime = row[1]
                    data_list.append((keytime, row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7], row[8], row[9], row[10]))

                report.write_artifact_data_table(data_headers, data_list, file_found)
                report.end_artifact_report()

                tsvname = f'Emulated Storage Metadata - Videos'
                tsv(self.report_folder, data_headers, data_list, tsvname)

                tlactivity = f'Emulated Storage Metadata - Videos'
                timeline(self.report_folder, tlactivity, data_list, data_headers)
            else:
                logfunc('No Emulated Storage Metadata Videos data available')

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
            from audio
            ''')

            all_rows = cursor.fetchall()
            usageentries = len(all_rows)
            if usageentries > 0:
                report = ArtifactHtmlReport('Audio - Emulated Storage Metadata')
                report.start_artifact_report(self.report_folder, 'Audio')
                report.add_script()
                data_headers = ('Key Timestamp','Date Added','Date Modified','Date Taken','Display Name','Size','Owner Package Name','Bucket Display Name','Relative Path','Is download?','Is favorite?','Is trashed?')
                data_list = []
                for row in all_rows:
                    if bool(row[0]):
                        keytime = row[0]
                    else:
                        keytime = row[1]
                    data_list.append((keytime, row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7], row[8], row[9], row[10]))

                report.write_artifact_data_table(data_headers, data_list, file_found)
                report.end_artifact_report()

                tsvname = f'Emulated Storage Metadata - Audio'
                tsv(self.report_folder, data_headers, data_list, tsvname)

                tlactivity = f'Emulated Storage Metadata - Audio'
                timeline(self.report_folder, tlactivity, data_list, data_headers)
            else:
                logfunc('No Emulated Storage Metadata Videos data available')

            db.close()

        return True
