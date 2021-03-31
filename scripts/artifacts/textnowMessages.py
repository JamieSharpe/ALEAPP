import datetime

from scripts.ilapfuncs import timeline, open_sqlite_db_readonly
from scripts.plugin_base import ArtefactPlugin
from scripts.ilapfuncs import logfunc, tsv
from scripts import artifact_report


class TextNowMessagesPlugin(ArtefactPlugin):
    """
    """

    def __init__(self):
        super().__init__()
        self.author = 'Unknown'
        self.author_email = ''
        self.author_url = ''

        self.category = 'Text Now'
        self.name = 'Messages'
        self.description = ''

        self.artefact_reference = ''  # Description on what the artefact is.
        self.path_filters = ['**/com.enflick.android.TextNow/databases/textnow_data.db*']  # Collection of regex search filters to locate an artefact.
        self.icon = 'message-square'  # feathricon for report.

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
                            SELECT CASE 
                                     WHEN messages.message_direction == 2 THEN NULL 
                                     WHEN contact_book_w_groups.to_addresses IS NULL THEN 
                                     messages.contact_value 
                                   END from_address, 
                                   CASE 
                                     WHEN messages.message_direction == 1 THEN NULL 
                                     WHEN contact_book_w_groups.to_addresses IS NULL THEN 
                                     messages.contact_value 
                                     ELSE contact_book_w_groups.to_addresses 
                                   END to_address, 
                                   CASE messages.message_direction
                                     WHEN 1 THEN "Incoming"
                                     ELSE "Outgoing" 
                                   END message_direction, 
                                   messages.message_text, 
                                   messages.READ, 
                                   messages.DATE/1000, 
                                   messages.attach, 
                                   thread_id 
                            FROM   (SELECT GM.contact_value, 
                                           Group_concat(GM.member_contact_value) AS to_addresses, 
                                           G.contact_value                       AS thread_id 
                                    FROM   group_members AS GM 
                                           join GROUPS AS G 
                                             ON G.contact_value = GM.contact_value 
                                    GROUP  BY GM.contact_value 
                                    UNION 
                                    SELECT contact_value, 
                                           NULL, 
                                           NULL 
                                    FROM   contacts) AS contact_book_w_groups 
                                   join messages 
                                     ON messages.contact_value = contact_book_w_groups.contact_value 
                            WHERE  message_type NOT IN ( 102, 100 ) 
                ''')

                all_rows = cursor.fetchall()
                usageentries = len(all_rows)
            except:
                usageentries = 0

            if usageentries > 0:

                data_headers = ('Send Timestamp', 'Message ID', 'From ID', 'To ID', 'Direction', 'Message', 'Read', 'Attachment')
                data_list = []
                for row in all_rows:
                    sendtime = datetime.datetime.fromtimestamp(int(row[5])).strftime('%Y-%m-%d %H:%M:%S')

                    data_list.append((sendtime, row[7], row[0], row[1], row[2], row[3], row[4], row[6]))

                artifact_report.GenerateHtmlReport(self, file_found, data_headers, data_list)

                tsv(self.report_folder, data_headers, data_list, self.full_name(), source_file_msg)

                timeline(self.report_folder, self.full_name(), data_list, data_headers)

            else:
                logfunc('No Text Now messages data available')

            db.close()

        return True
