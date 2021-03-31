import datetime

from scripts.ilapfuncs import open_sqlite_db_readonly
from scripts.plugin_base import ArtefactPlugin
from scripts.ilapfuncs import logfunc, tsv
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
               # source_file_friends = file_found.replace(self.seeker.directory, '')

            db = open_sqlite_db_readonly(imo_friends_db)
            cursor = db.cursor()
            try:
                cursor.execute('''
                             SELECT messages.buid AS buid, imdata, last_message, timestamp/1000000000, 
                                    case message_type when 1 then "Incoming" else "Outgoing" end message_type, message_read, name
                               FROM messages
                              INNER JOIN friends ON friends.buid = messages.buid
                ''')

                all_rows = cursor.fetchall()
                usageentries = len(all_rows)
            except:
                usageentries = 0

            if usageentries > 0:

                data_headers = ('build','imdata', 'last_message', 'timestamp', 'message_type', 'message_read', 'name') # Don't remove the comma, that is required to make this a tuple as there is only 1 element
                data_list = []
                for row in all_rows:
                    timestamp = datetime.datetime.fromtimestamp(int(row[3])).strftime('%Y-%m-%d %H:%M:%S')
                    data_list.append((row[0], row[1], row[2], timestamp, row[4], row[5], row[6]))

                artifact_report.GenerateHtmlReport(self, file_found, data_headers, data_list)

                tsv(self.report_folder, data_headers, data_list, self.full_name())

            else:
                logfunc('No IMO Messages found')

            db.close()

        return True
