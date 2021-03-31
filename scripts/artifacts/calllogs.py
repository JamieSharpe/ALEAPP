import os
import datetime

from scripts.ilapfuncs import timeline, open_sqlite_db_readonly, does_table_exist, logfunc, tsv
from scripts.plugin_base import ArtefactPlugin
from scripts import artifact_report


class CallLogPlugin(ArtefactPlugin):
    """
    """

    def __init__(self):
        super().__init__()
        self.author = 'Unknown'
        self.author_email = ''
        self.author_url = ''

        self.category = 'Call Logs'
        self.name = 'Call Logs (Alternative DBs)'
        self.description = ''

        self.artefact_reference = ''  # Description on what the artefact is.
        self.path_filters = ['**/com.android.providers.contacts/databases/contact*', '**/com.sec.android.provider.logsprovider/databases/logs.db*']  # Collection of regex search filters to locate an artefact.
        self.icon = 'phone'  # feathricon for report.

    def _processor(self) -> bool:

        source_file = ''
        for file_found in self.files_found:

            file_name = str(file_found)
            if not os.path.basename(file_name) == 'contacts2.db' and \
               not os.path.basename(file_name) == 'contacts.db' and \
               not os.path.basename(file_name) == 'logs.db':
                continue
            source_file = file_found.replace(self.seeker.directory, '')

            db = open_sqlite_db_readonly(file_name)
            calls_table_exists = does_table_exist(db, 'calls')
            cursor = db.cursor()
            try:
                if calls_table_exists:
                    cursor.execute('''
                        SELECT number, date/1000, (date/1000 + duration) as duration, 
                               case type when 1 then "Incoming"
                                         when 3 then "Incoming"
                                         when 2 then "Outgoing"
                                         when 5 then "Outgoing"
                                         else "Unknown" end as direction,
                                name FROM calls ORDER BY date DESC;''')
                else:
                    cursor.execute('''
                        SELECT number, date/1000, (date/1000 + duration) as duration, 
                               case type when 1 then "Incoming"
                                         when 3 then "Incoming"
                                         when 2 then "Outgoing"
                                         when 5 then "Outgoing"
                                         else "Unknown" end as direction,
                               name FROM logs ORDER BY date DESC;''')
                all_rows = cursor.fetchall()
                usageentries = len(all_rows)
            except Exception as e:
                print(e)
                usageentries = 0

            if usageentries > 0:

                data_headers = ('from_id', 'to_id','start_date', 'end_date', 'direction', 'name')
                data_list = []
                for row in all_rows:
                    callerId = None
                    calleeId = None
                    if row[3] == "Incoming":
                        callerId = row[0]
                    else:
                        calleeId = row[0]
                    starttime = datetime.datetime.fromtimestamp(int(row[2])).strftime('%Y-%m-%d %H:%M:%S')
                    endtime = datetime.datetime.fromtimestamp(int(row[2])).strftime('%Y-%m-%d %H:%M:%S')
                    data_list.append((callerId, calleeId, starttime, endtime, row[3], row[4]))

                artifact_report.GenerateHtmlReport(self, file_found, data_headers, data_list, allow_html = True)

                tsv(self.report_folder, data_headers, data_list, self.full_name(), source_file)

                timeline(self.report_folder, self.full_name(), data_list, data_headers)

            else:
                logfunc('No Call Logs found')

            db.close()

        return True
