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


class SmsMmsPlugin(ArtefactPlugin):
    """
    """

    def __init__(self):
        super().__init__()
        self.author = 'Unknown'
        self.author_email = ''
        self.author_url = ''

        self.name = 'MMS'
        self.description = ''

        self.artefact_reference = ''  # Description on what the artefact is.
        self.path_filters = ['**/com.android.providers.telephony/databases/mmssms*']  # Collection of regex search filters to locate an artefact.
        self.icon = ''  # feathricon for report.

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

            self.read_mms_messages(db, file_found)

            db.close()

        return True

    def read_mms_messages(self, db, file_found):

        mms_query = \
            '''
                SELECT pdu._id as mms_id, 
                    thread_id, 
                    CASE WHEN date>0 THEN datetime(pdu.date, 'UNIXEPOCH')
                         ELSE ""
                    END as date,
                    CASE WHEN date_sent>0 THEN datetime(pdu.date_sent, 'UNIXEPOCH')
                         ELSE ""
                    END as date_sent,
                    read,
                    (SELECT address FROM addr WHERE pdu._id=addr.msg_id and addr.type=0x89)as "FROM",
                    (SELECT address FROM addr WHERE pdu._id=addr.msg_id and addr.type=0x97)as "TO",
                    (SELECT address FROM addr WHERE pdu._id=addr.msg_id and addr.type=0x82)as "CC",
                    (SELECT address FROM addr WHERE pdu._id=addr.msg_id and addr.type=0x81)as "BCC",
                    CASE WHEN msg_box=1 THEN "Received" 
                         WHEN msg_box=2 THEN "Sent" 
                         ELSE msg_box 
                    END as msg_box,
                    part._id as part_id, seq, ct, cl, _data, text 
                FROM pdu LEFT JOIN part ON part.mid=pdu._id
                ORDER BY pdu._id, date, part_id 
            '''

        if self.report_folder[-1] == slash:
            folder_name = os.path.basename(self.report_folder[:-1])
        else:
            folder_name = os.path.basename(self.report_folder)

        cursor = db.cursor()
        cursor.execute(mms_query)
        all_rows = cursor.fetchall()
        entries = len(all_rows)
        if entries > 0:

            data_headers = ('Date', 'MSG ID', 'Thread ID', 'Date sent', 'Read',
                            'From', 'To', 'Cc', 'Bcc', 'Body')
            data_list = []

            last_id = 0
            temp_mms_list = []
            for row in all_rows:
                id = row['mms_id']
                if id != last_id:  # Start of new message, write out old message in temp buffer
                    self.add_mms_to_data_list(data_list, temp_mms_list, folder_name)
                    # finished writing
                    last_id = id
                    temp_mms_list = []

                msg = MmsMessage(row['date'], row['mms_id'], row['thread_id'],
                                 row['date_sent'], row['read'],
                                 row['FROM'], row['TO'], row['CC'], row['BCC'], row['msg_box'],
                                 row['part_id'], row['seq'], row['ct'], row['cl'],
                                 row['_data'], row['text'])
                temp_mms_list.append(msg)

                data_file_path = row['_data']
                if data_file_path == None:  # Has text, no file
                    msg.body = row['text']
                else:
                    # Get file from path
                    if data_file_path[0] == '/':
                        temp_path = data_file_path[1:]
                    else:
                        temp_path = data_file_path

                    path_parts = temp_path.split('/')
                    # This next routine reduces /data/xx/yy/img.jpg to /xx/yy/img.jpg removing the
                    # first folder in the path, so that if our root (starting point) is inside
                    # that folder, it will still find the file
                    if len(path_parts) > 2:
                        path_parts.pop(0)
                        temp_path = '/'.join(path_parts)

                    if is_windows:
                        temp_path = temp_path.replace('/', '\\')
                    data_file_path_regex = f'**{slash}' + temp_path

                    files_found = self.seeker.search(data_file_path_regex)
                    if files_found:
                        data_file_real_path = str(files_found[0])
                        shutil.copy2(data_file_real_path, self.report_folder)
                        data_file_name = os.path.basename(data_file_real_path)
                        msg.filename = data_file_name
                    else:
                        logfunc(f'File not found: {data_file_path}')
            # add last msg to list
            self.add_mms_to_data_list(data_list, temp_mms_list, folder_name)

            artifact_report.GenerateHtmlReport(self, file_found, data_headers, data_list)

            tsvname = f'mms messages'
            tsv(self.report_folder, data_headers, data_list, tsvname)

            tlactivity = f'MMS Messages'
            timeline(self.report_folder, tlactivity, data_list, data_headers)
        else:
            logfunc('No MMS messages found!')
            return False
        return True

    def add_mms_to_data_list(self, data_list, mms_list, folder_name):
        '''Reads messages from mms_list and adds valid mms messages to data_list'''
        for mms in mms_list:
            if mms.ct == 'application/smil':  # content type is smil, skipping this
                continue
            else:
                if mms.filename:
                    if mms.ct.find('image') >= 0:
                        body = '<a href="{1}/{0}"><img src="{1}/{0}" class="img-fluid z-depth-2 zoom" style="max-height: 400px" title="{0}"></a>'.format(
                            mms.filename, folder_name)
                    elif mms.ct.find('audio') >= 0:
                        body = '<audio controls><source src="{1}/{0}"></audio>'.format(mms.filename, folder_name)
                    elif mms.ct.find('video') >= 0:
                        body = '<video controls width="250"><source src="{1}/{0}"></video>'.format(mms.filename,
                                                                                                   folder_name)
                    else:
                        logfunc(f'Unknown body type, content type = {mms.ct}')
                        body = '<a href="{1}/{0}">{0}</a>'.format(mms.filename, folder_name)
                else:
                    body = mms.body

                mms_data = [mms.mms_id, mms.thread_id,
                            mms.date, mms.date_sent, mms.read,
                            mms.From, mms.to, mms.cc, mms.bcc,
                            body]
                data_list.append(mms_data)


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
