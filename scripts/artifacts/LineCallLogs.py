import datetime

from scripts.ilapfuncs import open_sqlite_db_readonly, logfunc, tsv, timeline
from scripts.plugin_base import ArtefactPlugin
from scripts import artifact_report


class LineCallLogsPlugin(ArtefactPlugin):
    """
    """

    def __init__(self):
        super().__init__()
        self.author = 'Unknown'
        self.author_email = ''
        self.author_url = ''

        self.category = 'Line'
        self.name = 'Call Logs'
        self.description = ''

        self.artefact_reference = ''  # Description on what the artefact is.
        self.path_filters = ['**/jp.naver.line.android/databases/**']  # Collection of regex search filters to locate an artefact.
        self.icon = 'phone'  # feathricon for report.

    def _processor(self) -> bool:

        source_file_call = ''
        line_call_db = ''
        line_msg_db = ''

        for file_found in self.files_found:

            file_name = str(file_found)
            if file_name.lower().endswith('naver_line'):
                line_msg_db = str(file_found)

            if file_name.lower().endswith('call_history'):
                line_call_db = str(file_found)
                source_file_call = file_found.replace(self.seeker.directory, '')

            db = open_sqlite_db_readonly(line_call_db)
            cursor = db.cursor()
            cursor.execute('''attach database "''' + line_msg_db + '''" as naver_line ''')
            try:
                cursor.execute('''
                            SELECT case Substr(calls.call_type, -1) when "O" then "Outgoing"
                                   else "Incoming" end AS direction, 
                                   calls.start_time/1000              AS start_time, 
                                   calls.end_time/1000                AS end_time, 
                                   case when Substr(calls.call_type, -1) = "O" then contact_book_w_groups.members 
                                   else null end AS group_members,  
                                   calls.caller_mid, 
                                   case calls.voip_type when "V" then "Video" 
                                      when "A" then "Audio"
                                      when "G" then calls.voip_gc_media_type 
                                   end   AS call_type
                            FROM   (SELECT id, 
                                           Group_concat(M.m_id) AS members 
                                    FROM   membership AS M 
                                    GROUP  BY id 
                                    UNION 
                                    SELECT m_id, 
                                           NULL 
                                    FROM   naver_line.contacts) AS contact_book_w_groups 
                                   JOIN call_history AS calls 
                                     ON calls.caller_mid = contact_book_w_groups.id
        
                ''')

                all_rows = cursor.fetchall()
                usageentries = len(all_rows)
            except:
                usageentries = 0

            if usageentries > 0:

                data_headers = ('Start Time', 'End Time', 'To ID', 'From ID', 'Direction', 'Call Type')
                data_list = []
                for row in all_rows:
                    start_time = datetime.datetime.fromtimestamp(int(row[1])).strftime('%Y-%m-%d %H:%M:%S')
                    end_time = datetime.datetime.fromtimestamp(int(row[2])).strftime('%Y-%m-%d %H:%M:%S')
                    data_list.append((start_time, end_time, row[3], row[4], row[0], row[5]))

                artifact_report.GenerateHtmlReport(self, file_found, data_headers, data_list)

                tsv(self.report_folder, data_headers, data_list, self.full_name(), source_file_call)

                timeline(self.report_folder, self.full_name(), data_list, data_headers)

            else:
                logfunc('No Line Call Logs found')

            db.close()

        return True
