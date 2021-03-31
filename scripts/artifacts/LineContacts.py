from scripts.ilapfuncs import timeline, open_sqlite_db_readonly
from scripts.plugin_base import ArtefactPlugin
from scripts.ilapfuncs import logfunc, tsv
from scripts import artifact_report


class LineContactsPlugin(ArtefactPlugin):
    """
    """

    def __init__(self):
        super().__init__()
        self.author = 'Unknown'
        self.author_email = ''
        self.author_url = ''

        self.category = 'Line'
        self.name = 'Contacts'
        self.description = ''

        self.artefact_reference = ''  # Description on what the artefact is.
        self.path_filters = ['**/jp.naver.line.android/databases/**']  # Collection of regex search filters to locate an artefact.
        self.icon = 'user'  # feathricon for report.

    def _processor(self) -> bool:

        source_file_msg = ''
        line_msg_db = ''

        for file_found in self.files_found:

            file_name = str(file_found)
            if file_name.lower().endswith('naver_line'):
                line_msg_db = str(file_found)
                source_file_msg = file_found.replace(self.seeker.directory, '')

            db = open_sqlite_db_readonly(line_msg_db)
            cursor = db.cursor()
            try:
                cursor.execute('''
                           SELECT m_id, server_name FROM   contacts
                ''')

                all_rows = cursor.fetchall()
                usageentries = len(all_rows)
            except:
                usageentries = 0

            if usageentries > 0:
                data_headers = ('user_id','user_name')
                data_list = []
                for row in all_rows:
                    data_list.append((row[0], row[1]))

                artifact_report.GenerateHtmlReport(self, file_found, data_headers, data_list)

                tsv(self.report_folder, data_headers, data_list, self.full_name(), source_file_msg)

                timeline(self.report_folder, self.full_name(), data_list, data_headers)

            else:
                logfunc('No Line Contact Logs found')

            db.close()

        return True
