import datetime

from scripts.ilapfuncs import timeline, open_sqlite_db_readonly
from scripts.plugin_base import ArtefactPlugin
from scripts.ilapfuncs import logfunc, tsv
from scripts import artifact_report


class WhatsAppGroupCallPlugin(ArtefactPlugin):
    """
    """

    def __init__(self):
        super().__init__()
        self.author = 'Unknown'
        self.author_email = ''
        self.author_url = ''

        self.category = 'WhatsApp'
        self.name = 'Group Call'
        self.description = ''

        self.artefact_reference = ''  # Description on what the artefact is.
        self.path_filters = ['**/com.whatsapp/databases/*.db*']  # Collection of regex search filters to locate an artefact.
        self.icon = 'phone'  # feathricon for report.

    def _processor(self) -> bool:

        source_file_msg = ''
        source_file_wa = ''
        whatsapp_msgstore_db = ''
        whatsapp_wa_db = ''

        for file_found in self.files_found:

            file_name = str(file_found)
            if file_name.endswith('msgstore.db'):
               whatsapp_msgstore_db = str(file_found)
               source_file_msg = file_found.replace(seeker.directory, '')

            db = open_sqlite_db_readonly(whatsapp_msgstore_db)
            cursor = db.cursor()
            try:
                cursor.execute('''
                SELECT case CL.video_call when 1 then "Video Call" else "Audio Call" end as call_type, 
                       CL.timestamp/1000 as start_time, 
                       ((cl.timestamp/1000) + CL.duration) as end_time, 
                       case CL.from_me when 0 then "Incoming" else "Outgoing" end as call_direction,
                       J1.raw_string AS from_id,
                                    group_concat(J.raw_string) AS group_members
                             FROM   call_log_participant_v2 AS CLP
                                    JOIN call_log AS CL
                                      ON CL._id = CLP.call_log_row_id
                                    JOIN jid AS J
                                      ON J._id = CLP.jid_row_id
                                    JOIN jid as J1
                                      ON J1._id = CL.jid_row_id
                                    GROUP  BY CL._id
                ''')

                all_rows = cursor.fetchall()
                usageentries = len(all_rows)
            except:
                usageentries = 0

            if usageentries > 0:
                data_headers = ('Start Time', 'End Time', 'Call Type', 'Call Direction', 'From ID', 'Group Members')
                data_list = []
                for row in all_rows:
                    starttime = datetime.datetime.fromtimestamp(int(row[1])).strftime('%Y-%m-%d %H:%M:%S')
                    endtime = datetime.datetime.fromtimestamp(int(row[2])).strftime('%Y-%m-%d %H:%M:%S')
                    data_list.append((starttime, endtime, row[0], row[3], row[4], row[5]))

                artifact_report.GenerateHtmlReport(self, file_found, data_headers, data_list)

                tsv(self.report_folder, data_headers, data_list, self.full_name(), source_file_msg)

                timeline(self.report_folder, self.full_name(), data_list, data_headers)

            else:
                logfunc('No Whatsapp Group Call Logs found')

            db.close()

        return True
