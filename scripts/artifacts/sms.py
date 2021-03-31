import os
import shutil
import sqlite3

from scripts.ilapfuncs import timeline, is_platform_windows, open_sqlite_db_readonly
from scripts.plugin_base import ArtefactPlugin
from scripts.artifact_report import ArtifactHtmlReport
from scripts.ilapfuncs import logfunc, tsv
from scripts import artifact_report

# Reference for flag values for mms:
# ----------------------------------
# https://developer.android.com/reference/android/provider/Telephony.Mms.Addr#TYPE
# https://android.googlesource.com/platform/frameworks/opt/mms/+/4bfcd8501f09763c10255442c2b48fad0c796baa/src/java/com/google/android/mms/pdu/PduHeaders.java


is_windows = is_platform_windows()
slash = '\\' if is_windows else '/'


class SmsPlugin(ArtefactPlugin):
    """
    """

    def __init__(self):
        super().__init__()
        self.author = 'Unknown'
        self.author_email = ''
        self.author_url = ''

        self.category = 'Messaging'
        self.name = 'SMS'
        self.description = ''

        self.artefact_reference = ''  # Description on what the artefact is.
        self.path_filters = ['**/com.android.providers.telephony/databases/mmssms*']  # Collection of regex search filters to locate an artefact.
        self.icon = 'message-square'  # feathricon for report.

    def _processor(self) -> bool:

        for file_found in self.files_found:
            file_found = str(file_found)

            if file_found.find('{0}mirror{0}'.format(slash)) >= 0:
                # Skip sbin/.magisk/mirror/data/.. , it should be duplicate data
                continue
            #elif file_found.find('{0}user_de{0}'.format(slash)) >= 0:
            #    # Skip data/user_de/0/com.android.providers.telephony/databases/mmssms.db, it is always empty
            #    continue
            elif not file_found.endswith('mmssms.db'):
                continue # Skip all other files

            db = open_sqlite_db_readonly(file_found)
            db.row_factory = sqlite3.Row # For fetching columns by name

            self.read_sms_messages(db, file_found)

            db.close()

        return True
        
    def read_sms_messages(self, db, file_found):
        sms_query = \
            '''
                SELECT _id as msg_id, thread_id, address, person, 
                    CASE WHEN date>0 THEN datetime(date/1000, 'UNIXEPOCH')
                         ELSE ""
                    END as date,
                    CASE WHEN date_sent>0 THEN datetime(date_sent/1000, 'UNIXEPOCH')
                         ELSE ""
                    END as date_sent,
                    read,
                    CASE WHEN type=1 THEN "Received"
                         WHEN type=2 THEN "Sent"
                         ELSE type 
                    END as type,
                    body, service_center, error_code
                FROM sms
                ORDER BY date
            '''

        cursor = db.cursor()
        cursor.execute(sms_query)
        all_rows = cursor.fetchall()
        entries = len(all_rows)
        if entries > 0:
            data_headers = ('Date','MSG ID', 'Thread ID', 'Address', 'Contact ID',
                'Date sent', 'Read', 'Type', 'Body', 'Service Center', 'Error code')
            data_list = []
            for row in all_rows:
                data_list.append((row['date'],row['msg_id'], row['thread_id'], row['address'],
                    row['person'],row['date_sent'], row['read'],
                    row['type'], row['body'], row['service_center'], row['error_code']))

            artifact_report.GenerateHtmlReport(self, file_found, data_headers, data_list)

            tsv(self.report_folder, data_headers, data_list, self.full_name())

            timeline(self.report_folder, self.name, data_list, data_headers)
        else:
            logfunc('No SMS messages found!')
            return False
        return True


class MmsMessage:
    def __init__(self, mms_id, thread_id, date, date_sent, read, From, to, cc, bcc, type, part_id, seq, ct, cl, data, text):
        self.mms_id = mms_id
        self.thread_id = thread_id
        self.date = date
        self.date_sent = date_sent
        self.read = read
        self.From = From
        self.to = to
        self.cc = cc
        self.bcc = bcc
        self.type = type
        self.part_id = part_id
        self.seq = seq
        self.ct = ct
        self.cl = cl
        self.data = data
        self.text = text
        # Added
        self.body = ''
        self.filename = ''
