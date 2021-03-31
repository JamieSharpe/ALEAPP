from scripts.ilapfuncs import timeline, open_sqlite_db_readonly
from scripts.plugin_base import ArtefactPlugin
from scripts.artifact_report import ArtifactHtmlReport
from scripts.ilapfuncs import logfunc, tsv
from scripts import artifact_report

class XenderContactsPlugin(ArtefactPlugin):
    """
    """

    def __init__(self):
        super().__init__()
        self.author = 'Unknown'
        self.author_email = ''
        self.author_url = ''

        self.name = 'Xender File Transfer - Contacts'
        self.description = ''

        self.artefact_reference = ''  # Description on what the artefact is.
        self.path_filters = [
            '**/cn.xender/databases/trans-history-db*'
        ]  # Collection of regex search filters to locate an artefact.
        self.icon = 'users'  # feathricon for report.

    def _processor(self) -> bool:

        for file_found in self.files_found:

            if file_found.endswith('-db'):
                continue

            db = open_sqlite_db_readonly(file_found)
            cursor = db.cursor()

            try:
                cursor.execute('''
                SELECT device_id, nick_name FROM profile WHERE connect_times = 0
                ''')

                all_rows = cursor.fetchall()
                usageentries = len(all_rows)
            except:
                usageentries = 0

            if usageentries > 0:
                data_headers = ('device_id','nick_name') # Don't remove the comma, that is required to make this a tuple as there is only 1 element
                data_list = []
                for row in all_rows:
                    data_list.append((row[0],row[1]))

                artifact_report.GenerateHtmlReport(self, file_found, data_headers, data_list)

                tsv(self.report_folder, data_headers, data_list, self.full_name())

            else:
                logfunc('No Xender Contacts found')

            db.close()
        return True
