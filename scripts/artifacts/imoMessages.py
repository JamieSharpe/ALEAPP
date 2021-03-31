import datetime
import json

from scripts.ilapfuncs import open_sqlite_db_readonly, logfunc, tsv, timeline
from scripts.plugin_base import ArtefactPlugin
from scripts import artifact_report


class ImoMessagesPlugin(ArtefactPlugin):
    """
    """

    def __init__(self):
        super().__init__()
        self.author = 'Unknown'
        self.author_email = ''
        self.author_url = ''

        self.category = 'IMO'
        self.name = 'Messages'
        self.description = ''

        self.artefact_reference = ''  # Description on what the artefact is.
        self.path_filters = ['**/com.imo.android.imous/databases/*.db*']  # Collection of regex search filters to locate an artefact.
        self.icon = 'message-square'  # feathricon for report.

    def _processor(self) -> bool:

        source_file_friends = ''
        for file_found in self.files_found:

            file_name = str(file_found)

            if file_name.endswith('imofriends.db'):
               imo_friends_db = str(file_found)
               source_file_friends = file_found.replace(self.seeker.directory, '')

            db = open_sqlite_db_readonly(imo_friends_db)
            cursor = db.cursor()
            try:
                cursor.execute('''
                             SELECT messages.buid AS buid, imdata, last_message, timestamp/1000000000, 
                                    case message_type when 1 then "Incoming" else "Outgoing" end message_type, message_read
                               FROM messages
                              INNER JOIN friends ON friends.buid = messages.buid
                ''')

                all_rows = cursor.fetchall()
                usageentries = len(all_rows)
            except:
                usageentries = 0

            if usageentries > 0:

                data_headers = ('Timestamp', 'From ID', 'To ID', 'Last Message', 'Direction', 'Message Read', 'Attachment')
                data_list = []

                for row in all_rows:
                    from_id = ''
                    to_id = ''
                    if row[4] == "Incoming":
                        from_id = row[0]
                    else:
                        to_id = row[0]
                    if row[1] is not None:
                        imdata_dict = json.loads(row[1])

                        # set to none if the key doesn't exist in the dict
                        attachmentOriginalPath = imdata_dict.get('original_path', None)
                        attachmentLocalPath = imdata_dict.get('local_path', None)
                        if attachmentOriginalPath:
                            attachmentPath = attachmentOriginalPath
                        else:
                            attachmentPath = attachmentLocalPath

                    timestamp = datetime.datetime.fromtimestamp(int(row[3])).strftime('%Y-%m-%d %H:%M:%S')
                    data_list.append((timestamp, from_id, to_id, row[2], row[4], row[5], attachmentPath))

                artifact_report.GenerateHtmlReport(self, file_found, data_headers, data_list)

                tsv(self.report_folder, data_headers, data_list, self.full_name(), source_file_friends)

                timeline(self.report_folder, self.full_name(), data_list, data_headers)

            else:
                logfunc('No IMO Messages found')

            db.close()

        return True
