import os

from scripts.ilapfuncs import timeline, get_next_unused_name, does_column_exist_in_db, open_sqlite_db_readonly
from scripts.plugin_base import ArtefactPlugin
from scripts.artifact_report import ArtifactHtmlReport
from scripts.ilapfuncs import logfunc, tsv
from scripts import artifact_report

class ChromeDownloadsPlugin(ArtefactPlugin):
    """
    """

    def __init__(self):
        super().__init__()
        self.author = 'Unknown'
        self.author_email = ''
        self.author_url = ''

        self.category = 'Chrome'
        self.name = 'Downloads'
        self.description = ''

        self.artefact_reference = ''  # Description on what the artefact is.
        self.path_filters = [
            '**/app_chrome/Default/History*',
            '**/app_sbrowser/Default/History*'
        ]  # Collection of regex search filters to locate an artefact.
        self.icon = ''  # feathricon for report.

        self.debug_mode = False

    def _processor(self) -> bool:

        for file_found in self.files_found:
            file_found = str(file_found)
            if not os.path.basename(file_found) == 'History': # skip -journal and other files
                continue
            browser_name = 'Chrome'
            if file_found.find('app_sbrowser') >= 0:
                browser_name = 'Browser'
            elif file_found.find('.magisk') >= 0 and file_found.find('mirror') >= 0:
                continue # Skip sbin/.magisk/mirror/data/.. , it should be duplicate data??

            db = open_sqlite_db_readonly(file_found)
            cursor = db.cursor()

            # check for last_access_time column, an older version of chrome db (32) does not have it
            if does_column_exist_in_db(db, 'downloads', 'last_access_time') == True:
                last_access_time_query = '''
                CASE last_access_time 
                    WHEN "0" 
                    THEN "" 
                    ELSE datetime(last_access_time / 1000000 + (strftime('%s', '1601-01-01')), "unixepoch")
                END AS "Last Access Time"'''
            else:
                last_access_time_query = "'' as last_access_query"

            cursor.execute(f'''
            SELECT 
            CASE start_time  
                WHEN "0" 
                THEN "" 
                ELSE datetime(start_time / 1000000 + (strftime('%s', '1601-01-01')), "unixepoch")
            END AS "Start Time", 
            CASE end_time 
                WHEN "0" 
                THEN "" 
                ELSE datetime(end_time / 1000000 + (strftime('%s', '1601-01-01')), "unixepoch")
            END AS "End Time", 
            {last_access_time_query},
            tab_url, 
            target_path, state, opened, received_bytes, total_bytes
            FROM downloads
            ''')

            all_rows = cursor.fetchall()
            usageentries = len(all_rows)
            if usageentries > 0:

                data_headers = ('Start Time','End Time','Last Access Time','URL','Target Path','State','Opened?','Received Bytes','Total Bytes')
                data_list = []
                for row in all_rows:
                    data_list.append((row[0],row[1],row[2],row[3],row[4],row[5],row[6],row[7],row[8]))
                artifact_report.GenerateHtmlReport(self, file_found, data_headers, data_list)

                tsvname = f'{browser_name} Downloads'
                tsv(self.report_folder, data_headers, data_list, tsvname)

                tlactivity = f'{browser_name} Downloads'
                timeline(self.report_folder, tlactivity, data_list, data_headers)
            else:
                logfunc(f'No {browser_name} download data available')

            db.close()
        return True
