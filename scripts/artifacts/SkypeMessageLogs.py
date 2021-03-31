import datetime
import os

from scripts.ilapfuncs import timeline, open_sqlite_db_readonly
from scripts.plugin_base import ArtefactPlugin
from scripts.ilapfuncs import logfunc, tsv
from scripts import artifact_report


class SkypeMessagesPlugin(ArtefactPlugin):
    """
    """

    def __init__(self):
        super().__init__()
        self.author = 'Unknown'
        self.author_email = ''
        self.author_url = ''

        self.category = 'Skype'
        self.name = 'Messages'
        self.description = ''

        self.artefact_reference = ''  # Description on what the artefact is.
        self.path_filters = ['**/com.skype.raider/databases/live*']  # Collection of regex search filters to locate an artefact.
        self.icon = 'message-square'  # feathricon for report.

    def _processor(self) -> bool:

        source_file = ''
        for file_found in self.files_found:

            file_name = str(file_found)
            if (('live' in file_name.lower()) and ('db-journal' not in file_name.lower())):
                skype_db = str(file_found)
                # File name has a format of live: which does not write out to a file system correctly
                # so this will fix it to the original name from what is actually written out.
                (head, tail) = os.path.split(file_found.replace(self.seeker.directory, ''))
                source_file = os.path.join(head, "live:" + tail[5:])
            else:
               continue

            db = open_sqlite_db_readonly(skype_db)
            cursor = db.cursor()

            try:
                cursor.execute('''
                SELECT contact_book_w_groups.conversation_id,
                               contact_book_w_groups.participant_ids,
                               messages.time/1000,
                               messages.content,
                               messages.device_gallery_path,
                               case messages.is_sender_me when 0 then "Incoming" else "Outgoing"
                               end is_sender_me, 
                               messages.person_id
                               FROM   (SELECT conversation_id,
                                       Group_concat(person_id) AS participant_ids
                                FROM   particiapnt
                                GROUP  BY conversation_id
                                UNION
                                SELECT entry_id as conversation_id,
                                       NULL
                                FROM   person) AS contact_book_w_groups
                               JOIN chatitem AS messages
                                 ON messages.conversation_link = contact_book_w_groups.conversation_id
                        WHERE message_type != 3
                ''')

                all_rows = cursor.fetchall()
                usageentries = len(all_rows)
            except:
                usageentries = 0

            if usageentries > 0:

                data_headers = ('thread_id', 'send_time', 'content', 'direction', 'from_id', 'to_id', 'attachment') # Don't remove the comma, that is required to make this a tuple as there is only 1 element
                data_list = []
                for row in all_rows:
                    thread_id = None
                    if row[1] == None:
                        thread_id  = row[0]
                    to_id = None
                    if row[5] == "Outgoing":
                        if row[1] == None:
                            to_id = None
                        elif ',' in row[1]:
                            to_id = row[1]
                        else:
                            to_id = row[0]
                    sendtime = datetime.datetime.fromtimestamp(int(row[2])).strftime('%Y-%m-%d %H:%M:%S')

                    data_list.append((thread_id, sendtime, row[3], row[5], row[6], to_id, row[4]))

                artifact_report.GenerateHtmlReport(self, file_found, data_headers, data_list)

                tsv(self.report_folder, data_headers, data_list, self.full_name(), source_file)

                timeline(self.report_folder, self.full_name(), data_list, data_headers)

            else:
                logfunc('No Skype messages data available')

            db.close()

        return True
