import os
import urllib.parse
import textwrap

from scripts.ilapfuncs import logfunc, tsv, timeline, get_next_unused_name, open_sqlite_db_readonly
from scripts.plugin_base import ArtefactPlugin
from scripts.artifact_report import ArtifactHtmlReport
from scripts.ilapfuncs import logfunc, tsv
from scripts import artifact_report

class ChromeWebSearchPlugin(ArtefactPlugin):
    """
    """

    def __init__(self):
        super().__init__()
        self.author = 'Unknown'
        self.author_email = ''
        self.author_url = ''

        self.category = 'Chrome'
        self.name = 'Web Search'
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
            cursor.execute('''
            SELECT
                url,
                title,
                visit_count,
                datetime(last_visit_time / 1000000 + (strftime('%s', '1601-01-01')), "unixepoch")
            FROM urls
            WHERE url like '%search?q=%'
            ''')

            all_rows = cursor.fetchall()
            usageentries = len(all_rows)
            if usageentries > 0:
                data_headers = ('Last Visit Time','Search Term','URL', 'Title', 'Visit Count')
                data_list = []
                for row in all_rows:
                    search = row[0].split('search?q=')[1].split('&')[0]
                    search = urllib.parse.unquote(search).replace('+', ' ')
                    if self.wrap_text:
                        data_list.append((row[3], search, (textwrap.fill(row[0], width=100)),row[1],row[2]))
                    else:
                        data_list.append((row[3], search, row[0], row[1], row[2]))

                artifact_report.GenerateHtmlReport(self, file_found, data_headers, data_list)

                tsvname = f'{browser_name} search terms'
                tsv(self.report_folder, data_headers, data_list, tsvname)

                tlactivity = f'{browser_name} Search Terms'
                timeline(self.report_folder, tlactivity, data_list, data_headers)
            else:
                logfunc(f'No {browser_name} web search terms data available')

            db.close()
        return True
