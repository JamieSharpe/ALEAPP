from scripts.ilapfuncs import timeline, open_sqlite_db_readonly
from scripts.plugin_base import ArtefactPlugin
from scripts.artifact_report import ArtifactHtmlReport
from scripts.ilapfuncs import logfunc, tsv
from scripts import artifact_report

class ZapyaPlugin(ArtefactPlugin):
    """
    """

    def __init__(self):
        super().__init__()
        self.author = 'Unknown'
        self.author_email = ''
        self.author_url = ''

        self.name = 'Zapya - File Transfer'
        self.description = ''

        self.artefact_reference = ''  # Description on what the artefact is.
        self.path_filters = ['**/com.dewmobile.kuaiya.play/databases/transfer20.db']  # Collection of regex search filters to locate an artefact.
        self.icon = 'file'  # feathricon for report.

    def _processor(self) -> bool:

        file_found = str(self.files_found[0])
        db = open_sqlite_db_readonly(file_found)
        cursor = db.cursor()
        cursor.execute('''
        SELECT device, name, direction, createtime/1000, path, title FROM transfer
        ''')

        all_rows = cursor.fetchall()
        usageentries = len(all_rows)
        if usageentries > 0:
            data_headers = ('Device', 'Name', 'direction', 'fromid', 'toid', 'createtime', 'path', 'title')  # Don't remove the comma, that is required to make this a tuple as there is only 1 element
            data_list = []
            for row in all_rows:
                from_id = ''
                to_id = ''
                if (row[2] == 1):
                    direction = 'Outgoing'
                    to_id = row[0]
                else:
                    direction = 'Incoming'
                    from_id = row[0]

                createtime = datetime.datetime.fromtimestamp(int(row[3])).strftime('%Y-%m-%d %H:%M:%S')
                data_list.append((row[0], row[1], direction, from_id, to_id, createtime, row[4], row[5]))

            artifact_report.GenerateHtmlReport(self, file_found, data_headers, data_list)

            tsv(self.report_folder, data_headers, data_list, self.full_name())

            timeline(self.report_folder, self.full_name(), data_list, data_headers)
        else:
            logfunc('No Zapya data available')

        db.close()
        return True
