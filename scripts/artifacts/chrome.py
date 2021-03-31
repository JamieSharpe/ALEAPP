import os
import textwrap

from scripts.ilapfuncs import timeline, get_next_unused_name, open_sqlite_db_readonly
from scripts.plugin_base import ArtefactPlugin
from scripts.artifact_report import ArtifactHtmlReport
from scripts.ilapfuncs import logfunc, tsv
from scripts import artifact_report

class ChromeHistoryPlugin(ArtefactPlugin):
    """
    """

    def __init__(self):
        super().__init__()
        self.author = 'Unknown'
        self.author_email = ''
        self.author_url = ''

        self.category = 'Chrome'
        self.name = 'History'
        self.description = ''

        self.artefact_reference = ''  # Description on what the artefact is.
        self.path_filters = [
            '**/app_chrome/Default/History*',
            '**/app_sbrowser/Default/History*'
        ]  # Collection of regex search filters to locate an artefact.
        self.icon = 'list'  # feathricon for report.

    def _processor(self) -> bool:

        for file_found in self.files_found:
            file_found = str(file_found)
            if not os.path.basename(file_found) == 'History': # skip -journal and other files
                continue
            elif file_found.find('.magisk') >= 0 and file_found.find('mirror') >= 0:
                continue # Skip sbin/.magisk/mirror/data/.. , it should be duplicate data??
            browser_name = self.get_browser_name(file_found)
            if file_found.find('app_sbrowser') >= 0:
                browser_name = 'Browser'

            db = open_sqlite_db_readonly(file_found)
            cursor = db.cursor()
            cursor.execute('''
            select
                datetime(last_visit_time / 1000000 + (strftime('%s', '1601-01-01')), "unixepoch"),
                url,
                title,
                visit_count,
                hidden
            from urls  
            ''')

            all_rows = cursor.fetchall()
            usageentries = len(all_rows)
            if usageentries > 0:
                data_headers = ('Last Visit Time','URL','Title','Visit Count','Hidden')
                data_list = []
                for row in all_rows:
                    if self.wrap_text:
                        data_list.append((textwrap.fill(row[0], width=100),row[1],row[2],row[3],row[4]))
                    else:
                        data_list.append((row[0],row[1],row[2],row[3],row[4]))
                artifact_report.GenerateHtmlReport(self, file_found, data_headers, data_list)

                tsv(self.report_folder, data_headers, data_list, self.full_name())

                timeline(self.report_folder, self.name, data_list, data_headers)
            else:
                logfunc(f'No {browser_name} history data available')

            db.close()

        return True

    def get_browser_name(self, file_name):

        if 'microsoft' in file_name.lower():
            return 'Edge'
        elif 'chrome' in file_name.lower():
            return 'Chrome'
        else:
            return 'Unknown'
