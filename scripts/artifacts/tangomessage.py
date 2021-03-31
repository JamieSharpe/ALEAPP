import sqlite3
import base64

from scripts.ilapfuncs import logfunc, tsv, timeline, open_sqlite_db_readonly

from scripts.plugin_base import ArtefactPlugin
from scripts.ilapfuncs import logfunc, tsv
from scripts import artifact_report


class TangoMessagesPlugin(ArtefactPlugin):
    """
    """

    def __init__(self):
        super().__init__()
        self.author = 'Unknown'
        self.author_email = ''
        self.author_url = ''

        self.category = 'Tango'
        self.name = 'Messages'
        self.description = ''

        self.artefact_reference = ''  # Description on what the artefact is.
        self.path_filters = ['**/com.sgiggle.production/files/tc.db*']  # Collection of regex search filters to locate an artefact.
        self.icon = 'message-square'  # feathricon for report.

    def _processor(self) -> bool:
    
        for file_found in self.files_found:
            file_found = str(file_found)

            if file_found.endswith('tc.db'):
                break

        # source_file = self.file_found.replace(seeker.directory, '')

        db = open_sqlite_db_readonly(file_found)
        cursor = db.cursor()
        try:
            cursor.execute('''
            SELECT conv_id, payload, create_time/1000 as create_time, 
                   case direction when 1 then "Incoming" else "Outgoing" end direction 
              FROM messages ORDER BY create_time DESC
            ''')

            all_rows = cursor.fetchall()
            usageentries = len(all_rows)
        except:
            usageentries = 0

        if usageentries > 0:

            data_headers = ('create_time', 'direction','message') # Don't remove the comma, that is required to make this a tuple as there is only 1 element
            data_list = []
            for row in all_rows:
                message = self._decodeMessage(row[0], row[1])
                data_list.append((row[2], row[3], message))

            artifact_report.GenerateHtmlReport(self, file_found, data_headers, data_list)

            tsv(self.report_folder, data_headers, data_list, self.full_name())

            timeline(self.report_folder, self.full_name(), data_list, data_headers)
        else:
            logfunc('No tangomessages data available')

        db.close()
        return True

    def _decodeMessage(self, wrapper, message):
        result = ""
        decoded = base64.b64decode(message)
        try:
            Z = decoded.decode("ascii", "ignore")
            result = Z.split(wrapper)[1]
        except Exception as ex:
            print("Error decoding a Tango message. " + str(ex))
            pass
        return result
