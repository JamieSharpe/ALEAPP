import os
from scripts.ilapfuncs import timeline, get_next_unused_name, open_sqlite_db_readonly
from scripts.plugin_base import ArtefactPlugin
from scripts.artifact_report import ArtifactHtmlReport
from scripts.ilapfuncs import logfunc, tsv
from scripts import artifact_report

class ChromeNetworkActionPredictorPlugin(ArtefactPlugin):
    """
    """

    def __init__(self):
        super().__init__()
        self.author = 'Unknown'
        self.author_email = ''
        self.author_url = ''

        self.category = 'Chrome'
        self.name = 'Network Action Predictor'
        self.description = ''

        self.artefact_reference = ''  # Description on what the artefact is.
        self.path_filters = [
            '**/app_Chrome/Default/Network Action Predictor*',
            '**/app_sbrowser/Default/Network Action Predictor*'
        ]  # Collection of regex search filters to locate an artefact.
        self.icon = ''  # feathricon for report.

    def _processor(self) -> bool:

        for file_found in self.files_found:
            file_found = str(file_found)
            if not file_found.endswith('Network Action Predictor'):
                continue # Skip all other files

            browser_name = 'Chrome'
            if file_found.find('app_sbrowser') >= 0:
                browser_name = 'Browser'
            elif file_found.find('.magisk') >= 0 and file_found.find('mirror') >= 0:
                continue # Skip sbin/.magisk/mirror/data/.. , it should be duplicate data??

            db = open_sqlite_db_readonly(file_found)
            cursor = db.cursor()
            cursor.execute('''
            select
            user_text,
            url,
            number_of_hits,
            number_of_misses
            from network_action_predictor
            ''')

            all_rows = cursor.fetchall()
            usageentries = len(all_rows)
            if usageentries > 0:
                data_headers = ('User Text','URL','Number of Hits','Number of Misses') # Don't remove the comma, that is required to make this a tuple as there is only 1 element
                data_list = []
                for row in all_rows:
                    data_list.append((row[0],row[1],row[2],row[3]))

                artifact_report.GenerateHtmlReport(self, file_found, data_headers, data_list)

                tsv(self.report_folder, data_headers, data_list, self.full_name())

                timeline(self.report_folder, self.name, data_list, data_headers)
            else:
                logfunc('No Browser Network Action Predictor data available')

            db.close()
        return True
