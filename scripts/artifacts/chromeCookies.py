import os
import textwrap

from scripts.ilapfuncs import timeline, get_next_unused_name, open_sqlite_db_readonly
from scripts.plugin_base import ArtefactPlugin
from scripts.artifact_report import ArtifactHtmlReport
from scripts.ilapfuncs import logfunc, tsv
from scripts import artifact_report

class ChromeCookiesPlugin(ArtefactPlugin):
    """
    """

    def __init__(self):
        super().__init__()
        self.author = 'Unknown'
        self.author_email = ''
        self.author_url = ''

        self.category = 'Chrome'
        self.name = 'Cookies'
        self.description = 'chrome'

        self.artefact_reference = ''  # Description on what the artefact is.
        self.path_filters = [
            '**/app_chrome/Default/Cookies*',
            '**/app_sbrowser/Default/Cookies*'
        ]  # Collection of regex search filters to locate an artefact.
        self.icon = ''  # feathricon for report.

    def _processor(self) -> bool:

        for file_found in self.files_found:
            file_found = str(file_found)
            if not os.path.basename(file_found) == 'Cookies': # skip -journal and other files
                continue
            browser_name = 'Chrome'
            if file_found.find('app_sbrowser') >= 0:
                browser_name = 'Browser'
            elif file_found.find('.magisk') >= 0 and file_found.find('mirror') >= 0:
                continue # Skip sbin/.magisk/mirror/data/.. , it should be duplicate data??

            db = open_sqlite_db_readonly(file_found)
            cursor = db.cursor()
            cursor.execute('''
            SELECT
            CASE
                last_access_utc 
                WHEN
                    "0" 
                THEN
                    "" 
                ELSE
                    datetime(last_access_utc / 1000000 + (strftime('%s', '1601-01-01')), "unixepoch")
            END AS "last_access_utc", 
            host_key,
            name,
            value,
            CASE
                creation_utc 
                WHEN
                    "0" 
                THEN
                    "" 
                ELSE
                    datetime(creation_utc / 1000000 + (strftime('%s', '1601-01-01')), "unixepoch")
            END AS "creation_utc", 
            CASE
                expires_utc 
                WHEN
                    "0" 
                THEN
                    "" 
                ELSE
                    datetime(expires_utc / 1000000 + (strftime('%s', '1601-01-01')), "unixepoch")
            END AS "expires_utc", 
            path
            FROM
            cookies
            ''')

            all_rows = cursor.fetchall()
            usageentries = len(all_rows)
            if usageentries > 0:
                data_headers = ('Last Access Date','Host','Name','Value','Created Date','Expiration Date','Path')
                data_list = []
                for row in all_rows:
                    if self.wrap_text:
                        data_list.append((row[0],row[1],(textwrap.fill(row[2], width=50)),row[3],row[4],row[5],row[6]))
                    else:
                        data_list.append((row[0],row[1],row[2],row[3],row[4],row[5],row[6]))

                artifact_report.GenerateHtmlReport(self, file_found, data_headers, data_list)

                tsv(self.report_folder, data_headers, data_list, self.full_name())

                timeline(self.report_folder, self.name, data_list, data_headers)
            else:
                logfunc(f'No {browser_name} cookies data available')

            db.close()

        return True
