import datetime

from scripts.ilapfuncs import timeline, open_sqlite_db_readonly
from scripts.plugin_base import ArtefactPlugin
from scripts.ilapfuncs import logfunc, tsv
from scripts import artifact_report


class WhatsAppContactsPlugin(ArtefactPlugin):
    """
    """

    def __init__(self):
        super().__init__()
        self.author = 'Unknown'
        self.author_email = ''
        self.author_url = ''

        self.category = 'WhatsApp'
        self.name = 'Contacts'
        self.description = ''

        self.artefact_reference = ''  # Description on what the artefact is.
        self.path_filters = ['*/com.whatsapp/databases/*.db*']  # Collection of regex search filters to locate an artefact.
        self.icon = 'user'  # feathricon for report.

    def _processor(self) -> bool:

        source_file_msg = ''
        source_file_wa = ''
        whatsapp_msgstore_db = ''
        whatsapp_wa_db = ''

        for file_found in self.files_found:

            file_name = str(file_found)

            if file_name.endswith('wa.db'):
               whatsapp_wa_db = str(file_found)
               source_file_wa = file_found.replace(self.seeker.directory, '')

        db = open_sqlite_db_readonly(whatsapp_wa_db)
        cursor = db.cursor()
        try:
            cursor.execute('''
                         SELECT jid, 
                                CASE 
                                  WHEN WC.number IS NULL THEN WC.jid 
                                  WHEN WC.number == "" THEN WC.jid 
                                  ELSE WC.number 
                                END number, 
                                CASE 
                                  WHEN WC.given_name IS NULL 
                                       AND WC.family_name IS NULL 
                                       AND WC.display_name IS NULL THEN WC.jid 
                                  WHEN WC.given_name IS NULL 
                                       AND WC.family_name IS NULL THEN WC.display_name 
                                  WHEN WC.given_name IS NULL THEN WC.family_name 
                                  WHEN WC.family_name IS NULL THEN WC.given_name 
                                  ELSE WC.given_name 
                                       || " " 
                                       || WC.family_name 
                                END name 
                         FROM   wa_contacts AS WC
            ''')

            all_rows = cursor.fetchall()
            usageentries = len(all_rows)
        except:
            usageentries = 0

        if usageentries > 0:

            data_headers = ('number','name') # Don't remove the comma, that is required to make this a tuple as there is only 1 element
            data_list = []
            for row in all_rows:
                data_list.append((row[0], row[1]))

            artifact_report.GenerateHtmlReport(self, file_found, data_headers, data_list)

            tsv(self.report_folder, data_headers, data_list, self.full_name(), source_file_wa)

        else:
            logfunc('No Whatsapp Contacts found')

        db.close()

        return
