import os
import sqlite3
import datetime

from scripts.artifact_report import ArtifactHtmlReport
from scripts.ilapfuncs import logfunc, tsv, timeline, is_platform_windows, open_sqlite_db_readonly, does_column_exist_in_db
from scripts.plugin_base import ArtefactPlugin
from scripts.artifact_report import ArtifactHtmlReport
from scripts.ilapfuncs import logfunc, tsv
from scripts import artifact_report

class PhoneContactsPlugin(ArtefactPlugin):
    """
    """

    def __init__(self):
        super().__init__()
        self.author = 'Unknown'
        self.author_email = ''
        self.author_url = ''

        self.category = 'Contacts'
        self.name = 'Phonebook Contacts'
        self.description = ''

        self.artefact_reference = ''  # Description on what the artefact is.
        self.path_filters = ['**/com.android.providers.contacts/databases/contacts*.db*']  # Collection of regex search filters to locate an artefact.
        self.icon = 'user'  # feathricon for report.

    def _processor(self) -> bool:

        source_file = ''
        for file_found in self.files_found:

            file_name = str(file_found)
            if not os.path.basename(file_name) == 'contacts2.db' and not os.path.basename(file_name) == 'contacts.db': # skip -journal and other files
                continue

            # FIXME: Not all seekers have a directory attribute.
            # source_file = file_found.replace(self.seeker.directory, '')

            db = open_sqlite_db_readonly(file_name)
            cursor = db.cursor()
            try:
                if does_column_exist_in_db(db, 'contacts', 'name_raw_contact_id'):
                    cursor.execute('''
                        SELECT mimetype, data1, name_raw_contact.display_name AS display_name
                          FROM raw_contacts JOIN contacts ON (raw_contacts.contact_id=contacts._id)
                          JOIN raw_contacts AS name_raw_contact ON(name_raw_contact_id=name_raw_contact._id) 
                          LEFT OUTER JOIN data ON (data.raw_contact_id=raw_contacts._id) 
                          LEFT OUTER JOIN mimetypes ON (data.mimetype_id=mimetypes._id) 
                         WHERE mimetype = 'vnd.android.cursor.item/phone_v2' OR mimetype = 'vnd.android.cursor.item/email_v2'
                         ORDER BY name_raw_contact.display_name ASC;''')
                else:
                    cursor.execute('''
                        SELECT mimetype, data1, raw_contacts.display_name AS display_name
                          FROM raw_contacts JOIN contacts ON (raw_contacts.contact_id=contacts._id)
                          LEFT OUTER JOIN data ON (data.raw_contact_id=raw_contacts._id)
                          LEFT OUTER JOIN mimetypes ON (data.mimetype_id=mimetypes._id)
                          WHERE mimetype = 'vnd.android.cursor.item/phone_v2' OR mimetype = 'vnd.android.cursor.item/email_v2'
                         ORDER BY raw_contacts.display_name ASC;''')

                all_rows = cursor.fetchall()
                usageentries = len(all_rows)
            except Exception as e:
                print (e)
                usageentries = 0

            if usageentries > 0:
                data_headers = ('mimetype','data1', 'display_name', 'phone_number', 'email address') # Don't remove the comma, that is required to make this a tuple as there is only 1 element
                data_list = []
                for row in all_rows:
                    phoneNumber = None
                    emailAddr = None
                    if row[0] == "vnd.android.cursor.item/phone_v2":
                        phoneNumber = row[1]
                    else:
                        emailAddr = row[1]

                    data_list.append((row[0], row[1], row[2], phoneNumber, emailAddr))

                artifact_report.GenerateHtmlReport(self, file_found, data_headers, data_list)

                # TODO: Add the paramter of the file analysed.
                tsv(self.report_folder, data_headers, data_list, self.full_name())

                timeline(self.report_folder, self.full_name(), data_list, data_headers)

            else:
                logfunc('No Contacts found')

            db.close()

        return
