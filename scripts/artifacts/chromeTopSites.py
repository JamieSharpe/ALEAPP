import os

from scripts.ilapfuncs import get_next_unused_name, open_sqlite_db_readonly
from scripts.plugin_base import ArtefactPlugin
from scripts.artifact_report import ArtifactHtmlReport
from scripts.ilapfuncs import logfunc, tsv
from scripts import artifact_report

class ChromeTopSitesPlugin(ArtefactPlugin):
    """
    """

    def __init__(self):
        super().__init__()
        self.author = 'Unknown'
        self.author_email = ''
        self.author_url = ''

        self.category = 'Chromium'
        self.name = 'Top sites'
        self.description = ''

        self.artefact_reference = ''  # Description on what the artefact is.
        self.path_filters = [
            '*/app_chrome/Default/Top Sites*',
            '*/app_sbrowser/Default/Top Sites*',
            '*/app_opera/Top Sites*'
        ]  # Collection of regex search filters to locate an artefact.
        self.icon = 'list'  # feathricon for report.

    def _processor(self) -> bool:
    
        for file_found in self.files_found:
            file_found = str(file_found)
            if not os.path.basename(file_found) == 'Top Sites': # skip -journal and other files
                continue
            browser_name = self.get_browser_name(file_found)
            if file_found.find('app_sbrowser') >= 0:
                browser_name = 'Browser'
            elif file_found.find('.magisk') >= 0 and file_found.find('mirror') >= 0:
                continue # Skip sbin/.magisk/mirror/data/.. , it should be duplicate data??

            db = open_sqlite_db_readonly(file_found)
            cursor = db.cursor()
            try:
                cursor.execute('''
                select
                url,
                url_rank,
                title,
                redirects
                FROM
                top_sites ORDER by url_rank asc
                ''')

                all_rows = cursor.fetchall()
                usageentries = len(all_rows)
            except:
                usageentries = 0

            if usageentries > 0:
                data_headers = ('URL','Rank','Title','Redirects')
                data_list = []
                for row in all_rows:
                    data_list.append((row[0],row[1],row[2],row[3]))

                artifact_report.GenerateHtmlReport(self, file_found, data_headers, data_list)

                tsv(self.report_folder, data_headers, data_list, self.full_name())
            else:
                logfunc(f'No {browser_name} Top Sites data available')

            db.close()

        return True

    def get_browser_name(self, file_name):

        if 'microsoft' in file_name.lower():
            return 'Edge'
        elif 'chrome' in file_name.lower():
            return 'Chrome'
        elif 'opera' in file_name.lower():
            return 'Opera'
        else:
            return 'Unknown'
