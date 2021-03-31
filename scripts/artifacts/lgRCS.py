import os

from scripts.ilapfuncs import timeline, is_platform_windows, open_sqlite_db_readonly, does_table_exist
from scripts.plugin_base import ArtefactPlugin
from scripts.artifact_report import ArtifactHtmlReport
from scripts.ilapfuncs import logfunc, tsv
from scripts import artifact_report

is_windows = is_platform_windows()
slash = '\\' if is_windows else '/' 


class LgRcsPlugin(ArtefactPlugin):
    """
    """

    def __init__(self):
        super().__init__()
        self.author = 'Unknown'
        self.author_email = ''
        self.author_url = ''

        self.name = 'RCS Chats - LG'
        self.description = ''

        self.artefact_reference = ''  # Description on what the artefact is.
        self.path_filters = ['*/mmssms.db*']  # Collection of regex search filters to locate an artefact.
        self.icon = ''  # feathricon for report.

    def _processor(self) -> bool:
        file_found = self.get_rcs_db_path()
        if not file_found:
            logfunc('Error: Could not get RCS chat database path for LG phones')
            return False

        if self.report_folder[-1] == slash:
            folder_name = os.path.basename(self.report_folder[:-1])
        else:
            folder_name = os.path.basename(self.report_folder)

        db = open_sqlite_db_readonly(file_found)
        if not does_table_exist(db, 'message'):
            logfunc('No RCS data in this db, \'message\' table is absent!')
            return False

        cursor = db.cursor()
        cursor.execute('''
        SELECT 
            CASE WHEN date>0 THEN datetime(date/1000, 'UNIXEPOCH')
                ELSE ""
            END as date,
            address, 
            body,
            read,
            message.thread_id, 
            is_file,
            file_name,
            file_path,
            file_size,
            thumb_file_path,
            thumb_file_size,
            file_xml_path
        FROM message
        left join file_info on  message.message_id = file_info.message_id
        ORDER BY date
            ''')

        all_rows = cursor.fetchall()
        usageentries = len(all_rows)
        if usageentries > 0:
            data_headers = ('Date','Address','Body','Read?','Thread ID','Is File?','Filename','File Path','File Size','Thumb File Path','Thumb File Size','File XML Path')
            data_list = []
            tsv_list = []

            for row in all_rows:
                data_list.append((row[0],row[1],row[2],row[3],row[4],row[5],row[6],row[7],row[8],row[9],row[10],row[11],))

            artifact_report.GenerateHtmlReport(self, file_found, data_headers, data_list)

            tsv(self.report_folder, data_headers, tsv_list, self.full_name())

            timeline(self.report_folder, self.name, tsv_list, data_headers)
        else:
            logfunc('No RCS Chats - LG data available')

        db.close()
        return

    def get_rcs_db_path(self):
        for file_found in self.files_found:
            file_found = str(file_found)
            if not os.path.basename(file_found) == 'mmssms.db':  # skip -journal and other files
                continue
            elif file_found.find('.magisk') >= 0 and file_found.find('mirror') >= 0:
                continue  # Skip sbin/.magisk/mirror/data/.. , it should be duplicate data??
            return file_found
        return ''

    def get_offline_path(self, files_found, blob_name):
        # offline_path_relative = "/files/shiny_blobs/blobs"
        for file_found in files_found:
            if file_found.endswith(blob_name):
                file_found = str(file_found)
                return file_found
        return ''
