from scripts.ilapfuncs import timeline, open_sqlite_db_readonly
from scripts.plugin_base import ArtefactPlugin
from scripts.artifact_report import ArtifactHtmlReport
from scripts.ilapfuncs import logfunc, tsv
from scripts import artifact_report

class ViberContactsPlugin(ArtefactPlugin):
    """
    """

    def __init__(self):
        super().__init__()
        self.author = 'Unknown'
        self.author_email = ''
        self.author_url = ''

        self.category = 'Viber'
        self.name = 'Contacts'
        self.description = ''

        self.artefact_reference = ''  # Description on what the artefact is.
        self.path_filters = ['**/com.viber.voip/databases/*']  # Collection of regex search filters to locate an artefact.
        self.icon = ''  # feathricon for report.

        self.debug_mode = False

    def _processor(self) -> bool:

        for file_found in self.files_found:

            if file_found.endswith('_data'):
                viber_data_db = str(file_found)

                db = open_sqlite_db_readonly(viber_data_db)
                cursor = db.cursor()

                try:
                    cursor.execute('''
                    SELECT
                    C.display_name,
                    coalesce(D.data2, D.data1, D.data3) as phone_number
                    FROM phonebookcontact AS C
                    JOIN phonebookdata AS D ON C._id = D.contact_id
                    ''')

                    all_rows = cursor.fetchall()
                    usageentries = len(all_rows)
                except:
                    usageentries = 0

                if usageentries > 0:
                    data_headers = ('Display Name','Phone Number') # Don't remove the comma, that is required to make this a tuple as there is only 1 element
                    data_list = []
                    for row in all_rows:
                        data_list.append((row[0], row[1]))

                    artifact_report.GenerateHtmlReport(self, file_found, data_headers, data_list)

                    tsv(self.report_folder, data_headers, data_list, self.name)

                else:
                    logfunc('No Viber Contacts data available')

                db.close()

        return True
