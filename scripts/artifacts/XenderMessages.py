import datetime

from scripts.ilapfuncs import timeline, open_sqlite_db_readonly
from scripts.plugin_base import ArtefactPlugin
from scripts.artifact_report import ArtifactHtmlReport
from scripts.ilapfuncs import logfunc, tsv
from scripts import artifact_report

class XenderMessagesPlugin(ArtefactPlugin):
    """
    """

    def __init__(self):
        super().__init__()
        self.author = 'Unknown'
        self.author_email = ''
        self.author_url = ''

        self.name = 'Xender File Transfer - Messages'
        self.description = ''

        self.artefact_reference = ''  # Description on what the artefact is.
        self.path_filters = ['*/cn.xender/databases/trans-history-db*']  # Collection of regex search filters to locate an artefact.
        self.icon = 'message-circle'  # feathricon for report.

    def _processor(self) -> bool:

        for file_found in self.files_found:

            if file_found.endswith('-db'):
                continue

            db = open_sqlite_db_readonly(file_found)
            cursor = db.cursor()

            try:
                cursor.execute('''
                        SELECT f_path, f_display_name, f_size_str, c_start_time/1000, c_direction, c_session_id, s_name, 
                               s_device_id, r_name, r_device_id
                          FROM new_history
                        ''')

                all_rows = cursor.fetchall()
                usageentries = len(all_rows)
            except:
                usageentries = 0

            if usageentries > 0:

                data_headers = (
                'file_path', 'file_display_name', 'file_size', 'timestamp', 'direction', 'to_id', 'from_id',
                'session_id', 'sender_name', 'sender_device_id', 'recipient_name',
                'recipient_device_id')

                data_list = []
                for row in all_rows:
                    from_id = ''
                    to_id = ''
                    if (row[4] == 1):
                        direction = 'Outgoing'
                        to_id = row[6]
                    else:
                        direction = 'Incoming'
                        from_id = row[6]

                    createtime = datetime.datetime.fromtimestamp(int(row[3])).strftime('%Y-%m-%d %H:%M:%S')

                    data_list.append((row[0], row[1], row[2], createtime, direction, to_id, from_id, row[5], row[6],
                                      row[7], row[8], row[9]))

                artifact_report.GenerateHtmlReport(self, file_found, data_headers, data_list)

                tsv(self.report_folder, data_headers, data_list, self.full_name())

                timeline(self.report_folder, self.name, data_list, data_headers)
            else:
                logfunc('No Xender file transfer messages data available')

            db.close()
        return True
