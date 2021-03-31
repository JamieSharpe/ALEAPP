import sqlite3
import textwrap

from scripts.plugin_base import ArtefactPlugin
from scripts.artifact_report import ArtifactHtmlReport
from scripts.ilapfuncs import logfunc, tsv, timeline, is_platform_windows, open_sqlite_db_readonly
from scripts import artifact_report

class FilesByGoogleSearchHistoryPlugin(ArtefactPlugin):
    """
    """

    def __init__(self):
        super().__init__()
        self.author = 'Unknown'
        self.author_email = ''
        self.author_url = ''

        self.name = 'Files by Google - Search History'
        self.description = ''

        self.artefact_reference = ''  # Description on what the artefact is.
        self.path_filters = ['**/com.google.android.apps.nbu.files/databases/search_history_database*']  # Collection of regex search filters to locate an artefact.
        self.icon = ''  # feathricon for report.

        self.debug_mode = False

    def _processor(self) -> bool:

        for file_found in self.files_found:
            file_found = str(file_found)
            if not file_found.endswith('search_history_database'):
                continue # Skip all other files

            db = open_sqlite_db_readonly(file_found)
            cursor = db.cursor()
            cursor.execute('''
            select
                searched_term,
                case timestamp
                    when 0 then ''
                    else datetime(timestamp/1000,'unixepoch')
                end as timestamp
            from search_history_content
            ''')

            all_rows = cursor.fetchall()
            usageentries = len(all_rows)
            if usageentries > 0:
                data_headers = ('Search Term','Timestamp') # Don't remove the comma, that is required to make this a tuple as there is only 1 element
                data_list = []
                for row in all_rows:
                    data_list.append((row[0],row[1]))

                artifact_report.GenerateHtmlReport(self, file_found, data_headers, data_list)

                tsvname = f'Files By Google - Search History'
                tsv(self.report_folder, data_headers, data_list, tsvname)

                tlactivity = f'Files By Google - Search History'
                timeline(self.report_folder, tlactivity, data_list, data_headers)
            else:
                logfunc('No Files By Google - Search History data available')

        db.close()
        return
