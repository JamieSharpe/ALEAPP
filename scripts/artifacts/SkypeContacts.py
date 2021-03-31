import os

from scripts.ilapfuncs import open_sqlite_db_readonly
from scripts.plugin_base import ArtefactPlugin
from scripts.ilapfuncs import logfunc, tsv
from scripts import artifact_report


class SkypeContactsPlugin(ArtefactPlugin):
    """
    """

    def __init__(self):
        super().__init__()
        self.author = 'Unknown'
        self.author_email = ''
        self.author_url = ''

        self.category = 'Skype'
        self.name = 'Contacts'
        self.description = ''

        self.artefact_reference = ''  # Description on what the artefact is.
        self.path_filters = ['**/com.skype.raider/databases/live*']  # Collection of regex search filters to locate an artefact.
        self.icon = 'user'  # feathricon for report.

    def _processor(self) -> bool:

        source_file = ''
        for file_found in self.files_found:

            file_name = str(file_found)
            if (('live' in file_name.lower()) and ('db-journal' not in file_name.lower())):
                skype_db = str(file_found)
                # File name has a format of live: which does not write out to a file system correctly
                # so this will fix it to the original name from what is actually written out.
                (head, tail) = os.path.split(file_found.replace(self.seeker.directory, ''))
                source_file = os.path.join(head, "live:" + tail[5:])
            else:
               continue

            db = open_sqlite_db_readonly(skype_db)
            cursor = db.cursor()

            try:
                cursor.execute('''
                        SELECT entry_id, 
                               CASE
                                 WHEN Ifnull(first_name, "") == "" AND Ifnull(last_name, "") == "" THEN entry_id
                                 WHEN first_name is NULL THEN replace(last_name, ",", "")
                                 WHEN last_name is NULL THEN replace(first_name, ",", "")
                                 ELSE replace(first_name, ",", "") || " " || replace(last_name, ",", "")
                               END AS name
                        FROM   person 
                ''')

                all_rows = cursor.fetchall()
                usageentries = len(all_rows)
            except:
                usageentries = 0

            if usageentries > 0:

                data_headers = ('Entry ID', 'Name')
                data_list = []
                for row in all_rows:
                    data_list.append((row[0], row[1]))

                artifact_report.GenerateHtmlReport(self, file_found, data_headers, data_list)

                tsv(self.report_folder, data_headers, data_list, self.full_name(), source_file)

            else:
                logfunc('No Skype Contacts found')

            db.close()

        return True
