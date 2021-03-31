from scripts.ilapfuncs import timeline, open_sqlite_db_readonly
from scripts.plugin_base import ArtefactPlugin
from scripts.artifact_report import ArtifactHtmlReport
from scripts.ilapfuncs import logfunc, tsv


class XenderPlugin(ArtefactPlugin):
    """
    """

    def __init__(self):
        super().__init__()
        self.author = 'Unknown'
        self.author_email = ''
        self.author_url = ''

        self.name = 'File Transfer'
        self.description = ''

        self.artefact_reference = ''  # Description on what the artefact is.
        self.path_filters = [
            '**/cn.xender/databases/trans-history-db*'
        ]  # Collection of regex search filters to locate an artefact.
        self.icon = ''  # feathricon for report.

    def _processor(self) -> bool:


        for file_found in self.files_found:
            file_found = str(file_found)

            if file_found.endswith('-db'):
                break

        db = open_sqlite_db_readonly(file_found)
        cursor = db.cursor()
        try:
            cursor.execute('''
            SELECT device_id, nick_name FROM profile WHERE connect_times = 0
            ''')

            all_rows = cursor.fetchall()
            usageentries = len(all_rows)
        except:
            usageentries = 0

        if usageentries > 0:
            report = ArtifactHtmlReport('Xender file transfer - contacts')
            report.start_artifact_report(self.report_folder, 'Xender file transfer - contacts')
            report.add_script()
            data_headers = ('device_id','nick_name') # Don't remove the comma, that is required to make this a tuple as there is only 1 element
            data_list = []
            for row in all_rows:
                data_list.append((row[0],row[1]))

            report.write_artifact_data_table(data_headers, data_list, file_found)
            report.end_artifact_report()

            tsvname = f'Xender file transfer - contacts'
            tsv(self.report_folder, data_headers, data_list, tsvname)

        else:
            logfunc('No Xender Contacts found')

        try:
            cursor.execute('''
            SELECT f_path, f_display_name, f_size_str, c_start_time, case c_direction when 1 then "Outgoing" else "Incoming" end direction, 
                   c_session_id, s_name, s_device_id, r_name, r_device_id
              FROM new_history
            ''')

            all_rows = cursor.fetchall()
            usageentries = len(all_rows)
        except:
            usageentries = 0

        if usageentries > 0:
            report = ArtifactHtmlReport('Xender file transfer - Messages')
            report.start_artifact_report(self.report_folder, 'Xender file transfer - Messages')
            report.add_script()
            data_headers = ('file_path','file_display_name','file_size','timestamp','direction', 'session_id', 'sender_name', 'sender_device_id', 'recipient_name', 'recipient_device_id' ) # Don't remove the comma, that is required to make this a tuple as there is only 1 element
            data_list = []
            for row in all_rows:
                data_list.append((row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7], row[8], row[9]))

            report.write_artifact_data_table(data_headers, data_list, file_found)
            report.end_artifact_report()

            tsvname = f'Xender file transfer - Messages'
            tsv(self.report_folder, data_headers, data_list, tsvname)

            tlactivity = f'Xender file transfer - Messages'
            timeline(self.report_folder, tlactivity, data_list, data_headers)
        else:
            logfunc('No Xender file transfer messages data available')

        db.close()
        return True
