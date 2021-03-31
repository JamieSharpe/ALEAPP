import os
import textwrap

from scripts.ilapfuncs import timeline, get_next_unused_name, open_sqlite_db_readonly
from scripts.plugin_base import ArtefactPlugin
from scripts.artifact_report import ArtifactHtmlReport
from scripts.ilapfuncs import logfunc, tsv


class ChromeSearchTermsPlugin(ArtefactPlugin):
    """
    """

    def __init__(self):
        super().__init__()
        self.author = 'Unknown'
        self.author_email = ''
        self.author_url = ''

        self.name = 'Chrome Search Terms Plugin'
        self.description = ''

        self.artefact_reference = ''  # Description on what the artefact is.
        self.path_filters = [
            '**/app_chrome/Default/History*',
            '**/app_sbrowser/Default/History*'
        ]  # Collection of regex search filters to locate an artefact.
        self.icon = ''  # feathricon for report.

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
                url_id,
                term,
                id,
                url,
                datetime(last_visit_time / 1000000 + (strftime('%s', '1601-01-01')), "unixepoch")
            FROM keyword_search_terms, urls
            WHERE url_id = id
            ''')

            all_rows = cursor.fetchall()
            usageentries = len(all_rows)
            if usageentries > 0:
                report = ArtifactHtmlReport(f'{browser_name} Keyword Search Terms')
                #check for existing and get next name for report file, so report from another file does not get overwritten
                report_path = os.path.join(self.report_folder, f'{browser_name} Keyword Search Terms.temphtml')
                report_path = get_next_unused_name(report_path)[:-9] # remove .temphtml
                report.start_artifact_report(self.report_folder, os.path.basename(report_path))
                report.add_script()
                data_headers = ('Last Visit Time','Term','URL')
                data_list = []
                for row in all_rows:
                    if self.wrap_text:
                        data_list.append((row[4], row[1],(textwrap.fill(row[3], width=100))))
                    else:
                        data_list.append((row[4], row[1], row[3]))

                report.write_artifact_data_table(data_headers, data_list, file_found)
                report.end_artifact_report()

                tsvname = f'{browser_name} keyword search terms'
                tsv(self.report_folder, data_headers, data_list, tsvname)

                tlactivity = f'{browser_name} Keyword Search Terms'
                timeline(self.report_folder, tlactivity, data_list, data_headers)
            else:
                logfunc(f'No {browser_name} keyword search terms data available')

            db.close()

        return True
