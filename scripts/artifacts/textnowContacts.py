from scripts.ilapfuncs import open_sqlite_db_readonly
from scripts.plugin_base import ArtefactPlugin
from scripts.ilapfuncs import logfunc, tsv
from scripts import artifact_report


class TextNowContactsPlugin(ArtefactPlugin):
    """
    """

    def __init__(self):
        super().__init__()
        self.author = 'Unknown'
        self.author_email = ''
        self.author_url = ''

        self.category = 'Text Now'
        self.name = 'Contacts'
        self.description = ''

        self.artefact_reference = ''  # Description on what the artefact is.
        self.path_filters = ['**/com.enflick.android.TextNow/databases/textnow_data.db*']  # Collection of regex search filters to locate an artefact.
        self.icon = 'user'  # feathricon for report.

    def _processor(self) -> bool:

        source_file_msg = ''

        for file_found in self.files_found:

            file_name = str(file_found)
            if file_name.endswith('textnow_data.db'):
               textnow_db = str(file_found)
               source_file_msg = file_found.replace(self.seeker.directory, '')

            db = open_sqlite_db_readonly(textnow_db)
            cursor = db.cursor()

            try:
                cursor.execute('''
                             SELECT C.contact_value AS number,  
                                    CASE 
                                      WHEN contact_name IS NULL THEN contact_value 
                                      WHEN contact_name == "" THEN contact_value 
                                      ELSE contact_name 
                                    END             name 
                             FROM   contacts AS C        ''')

                all_rows = cursor.fetchall()
                usageentries = len(all_rows)
            except:
                usageentries = 0

            if usageentries > 0:

                data_headers = ('Number', 'Name')
                data_list = []
                for row in all_rows:
                    data_list.append((row[0], row[1]))

                artifact_report.GenerateHtmlReport(self, file_found, data_headers, data_list)

                tsv(self.report_folder, data_headers, data_list, self.full_name(), source_file_msg)

            else:
                logfunc('No Text Now Contacts found')

            db.close()

        return True
