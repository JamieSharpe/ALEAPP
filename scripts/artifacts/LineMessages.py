import datetime

from scripts.ilapfuncs import timeline, open_sqlite_db_readonly
from scripts.plugin_base import ArtefactPlugin
from scripts.ilapfuncs import logfunc, tsv
from scripts import artifact_report


class LineMessagesPlugin(ArtefactPlugin):
    """
    """

    def __init__(self):
        super().__init__()
        self.author = 'Unknown'
        self.author_email = ''
        self.author_url = ''

        self.category = 'Line'
        self.name = 'Messages'
        self.description = ''

        self.artefact_reference = ''  # Description on what the artefact is.
        self.path_filters = ['**/jp.naver.line.android/databases/**']  # Collection of regex search filters to locate an artefact.
        self.icon = 'message-square'  # feathricon for report.

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
                            SELECT contact_book_w_groups.id, 
                                   contact_book_w_groups.members, 
                                   messages.from_mid, 
                                   messages.content, 
                                   messages.created_time/1000, 
                                   messages.attachement_type, 
                                   messages.attachement_local_uri, 
                                   case messages.status when 1 then "Incoming" 
                                   else "Outgoing" end status                           
                            FROM   (SELECT id, 
                                           Group_concat(M.m_id) AS members 
                                    FROM   membership AS M 
                                    GROUP  BY id 
                                    UNION 
                                    SELECT m_id, 
                                           NULL 
                                    FROM   contacts) AS contact_book_w_groups 
                                   JOIN chat_history AS messages 
                                     ON messages.chat_id = contact_book_w_groups.id 
                            WHERE  attachement_type != 6
                ''')

                all_rows = cursor.fetchall()
                usageentries = len(all_rows)
            except:
                usageentries = 0

            if usageentries > 0:

                data_headers = ('start_time','from_id', 'to_id', 'direction', 'thread_id', 'message', 'attachments')
                data_list = []
                for row in all_rows:
                    thread_id = None
                    if row[1] == None:
                        thread_id = row[0]
                    to_id = None
                    if row[4] == "Outgoing":
                        if ',' in row[1]:
                            to_id = row[1]
                        else:
                            to_id = row[0]
                    attachment = row[6]
                    if row[6] is None:
                        attachment = None
                    elif 'content' in row[6]:
                        attachment = None
                    created_time = datetime.datetime.fromtimestamp(int(row[4])).strftime('%Y-%m-%d %H:%M:%S')
                    data_list.append((created_time, row[2], to_id, row[7], thread_id, row[3], attachment))

                artifact_report.GenerateHtmlReport(self, file_found, data_headers, data_list)

                tsv(self.report_folder, data_headers, data_list, self.full_name(), source_file_msg)

                timeline(self.report_folder, self.full_name(), data_list, data_headers)

            else:
                logfunc('No Line messages available')

            db.close()

        return True
