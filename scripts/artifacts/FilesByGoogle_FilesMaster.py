import sqlite3
import textwrap

from scripts.plugin_base import ArtefactPlugin
from scripts.ilapfuncs import *
from scripts import search_files
from scripts.artifact_report import ArtifactHtmlReport
from scripts.ilapfuncs import logfunc, tsv, timeline, is_platform_windows, open_sqlite_db_readonly
from scripts import artifact_report

class FilesByGoogleFilesMasterPlugin(ArtefactPlugin):
    """
    """

    def __init__(self):
        super().__init__()
        self.author = 'Unknown'
        self.author_email = ''
        self.author_url = ''

        self.name = 'Files by Google - Files Master'
        self.description = ''

        self.artefact_reference = ''  # Description on what the artefact is.
        self.path_filters = ['**/com.google.android.apps.nbu.files/databases/files_master_database*']  # Collection of regex search filters to locate an artefact.
        self.icon = 'file'  # feathricon for report.

    def _processor(self) -> bool:

        for file_found in self.files_found:
            file_found = str(file_found)
            if not file_found.endswith('files_master_database'):
                continue # Skip all other files

            db = open_sqlite_db_readonly(file_found)
            cursor = db.cursor()
            cursor.execute('''
            select
                root_path,
                root_relative_file_path,
                file_name,
                size,
                case file_date_modified_ms
                    when 0 then ''
                    else datetime(file_date_modified_ms/1000,'unixepoch')
                end as file_date_modified_ms,
                mime_type,
                case media_type
                    when 0 then 'App/Data'
                    when 1 then 'Picture'
                    when 2 then 'Audio'
                    when 3 then 'Video'
                    when 6 then 'Text'
                end as media_type,
                uri,
                case is_hidden
                    when 0 then ''
                    when 1 then 'Yes'
                end as is_hidden,
                title,
                parent_folder_name
            from files_master_table
            ''')

            all_rows = cursor.fetchall()
            usageentries = len(all_rows)
            if usageentries > 0:
                data_headers = ('Root Path','Root Relative Path','File Name','Size','Date Modified','Mime Type','Media Type','URI','Hidden','Title','Parent Folder') # Don't remove the comma, that is required to make this a tuple as there is only 1 element
                data_list = []
                for row in all_rows:
                    data_list.append((row[0],row[1],row[2],row[3],row[4],row[5],row[6],row[7],row[8],row[9],row[10]))

                artifact_report.GenerateHtmlReport(self, file_found, data_headers, data_list)

                tsv(self.report_folder, data_headers, data_list, self.full_name())

                timeline(self.report_folder, self.name, data_list, data_headers)
            else:
                logfunc('No Files By Google - Files Master data available')

        db.close()
        return True
