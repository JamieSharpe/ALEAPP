import datetime
from scripts.ilapfuncs import timeline, open_sqlite_db_readonly
from scripts.plugin_base import ArtefactPlugin
from scripts.ilapfuncs import logfunc, tsv
from scripts import artifact_report


class ShareItPlugin(ArtefactPlugin):
    """
    """

    def __init__(self):
        super().__init__()
        self.author = 'Unknown'
        self.author_email = ''
        self.author_url = ''

        self.category = 'Share It'
        self.name = 'File Transfer'
        self.description = ''

        self.artefact_reference = ''  # Description on what the artefact is.
        self.path_filters = ['**/com.lenovo.anyshare.gps/databases/history.db*']  # Collection of regex search filters to locate an artefact.
        self.icon = 'file-text'  # feathricon for report.

    def _processor(self) -> bool:
    
        for file_found in self.files_found:

            if file_found.endswith('history.db'):
                break

        source_file = file_found.replace(self.seeker.directory, '')

        db = open_sqlite_db_readonly(file_found)
        cursor = db.cursor()
        try:
            cursor.execute('''
            SELECT case history_type when 1 then "Incoming" else "Outgoing" end direction,
                   case history_type when 1 then device_id else null end from_id,
                   case history_type when 1 then null else device_id end to_id,
                   device_name, description, timestamp/1000 as timestamp, file_path
                                    FROM history
                                    JOIN item where history.content_id = item.item_id
            ''')

            all_rows = cursor.fetchall()
            usageentries = len(all_rows)
        except:
            usageentries = 0

        if usageentries > 0:

            data_headers = ('direction', 'from_id', 'to_id', 'device_name', 'description', 'timestamp', 'file_path')  #
            data_list = []
            for row in all_rows:
                timestamp = datetime.datetime.fromtimestamp(int(row[5])).strftime('%Y-%m-%d %H:%M:%S')
                data_list.append((row[0], row[1], row[2], row[3], row[4], timestamp, row[6]))
            artifact_report.GenerateHtmlReport(self, file_found, data_headers, data_list)

            tsv(self.report_folder, data_headers, data_list, self.full_name(), source_file)

            timeline(self.report_folder, self.full_name(), data_list, data_headers)
        else:
            logfunc('No Shareit file transfer data available')

        db.close()

        return True
