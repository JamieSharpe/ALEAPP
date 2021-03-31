import datetime

from scripts.ilapfuncs import timeline, open_sqlite_db_readonly
from scripts.plugin_base import ArtefactPlugin
from scripts.ilapfuncs import logfunc, tsv
from scripts import artifact_report


class TextNowCallLogsPlugin(ArtefactPlugin):
    """
    """

    def __init__(self):
        super().__init__()
        self.author = 'Unknown'
        self.author_email = ''
        self.author_url = ''

        self.category = 'Text Now'
        self.name = 'Call Logs'
        self.description = ''

        self.artefact_reference = ''  # Description on what the artefact is.
        self.path_filters = ['**/com.enflick.android.TextNow/databases/textnow_data.db*']  # Collection of regex search filters to locate an artefact.
        self.icon = 'phone'  # feathricon for report.

    def _processor(self) -> bool:

        source_file_msg = ''

        for file_found in self.files_found:

            file_name = str(file_found)
            if file_name.endswith('textnow_data.db'):
               textnow_db = str(file_found)
               source_file_msg = file_found.replace(self.seeker.directory, '')

            db = open_sqlite_db_readonly(textnow_db)
            cursor = db.cursor()
            try:
                cursor.execute('''
                            SELECT contact_value     AS num, 
                                   case message_direction when 2 then "Outgoing" else "Incoming" end AS direction, 
                                    date/1000 + message_text      AS duration, 
                                    date/1000              AS datetime 
                              FROM  messages AS M 
                             WHERE  message_type IN ( 100, 102 )
                ''')

                all_rows = cursor.fetchall()
                usageentries = len(all_rows)
            except:
                usageentries = 0

            if usageentries > 0:

                data_headers = ('Start Time', 'End Time', 'From ID', 'To ID', 'Call Direction')
                data_list = []
                for row in all_rows:
                    phone_number_from = None
                    phone_number_to = None
                    if row[1] == "Outgoing":
                        phone_number_to = row[0]
                    else:
                        phone_number_from = row[0]
                    starttime = datetime.datetime.fromtimestamp(int(row[3])).strftime('%Y-%m-%d %H:%M:%S')
                    endtime = datetime.datetime.fromtimestamp(int(row[2])).strftime('%Y-%m-%d %H:%M:%S')
                    data_list.append((starttime, endtime, phone_number_from, phone_number_to, row[1]))

                artifact_report.GenerateHtmlReport(self, file_found, data_headers, data_list)

                tsv(self.report_folder, data_headers, data_list, self.full_name(), source_file_msg)

                timeline(self.report_folder, self.full_name(), data_list, data_headers)

            else:
                logfunc('No Text Now Call Logs found')

            db.close()

        return True
