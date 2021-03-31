import datetime
import os
import re

from Crypto.Cipher import AES
from Crypto.Protocol.KDF import PBKDF2
from scripts.ilapfuncs import timeline, get_next_unused_name, open_sqlite_db_readonly
from scripts.plugin_base import ArtefactPlugin
from scripts.artifact_report import ArtifactHtmlReport
from scripts.ilapfuncs import logfunc, tsv
from scripts import artifact_report

class ChromeLoginDataPlugin(ArtefactPlugin):
    """
    """

    def __init__(self):
        super().__init__()
        self.author = 'Unknown'
        self.author_email = ''
        self.author_url = ''

        self.category = 'Chrome'
        self.name = 'Login Data'
        self.description = ''

        self.artefact_reference = ''  # Description on what the artefact is.
        self.path_filters = [
            '**/app_chrome/Default/Login Data*',
            '**/app_sbrowser/Default/Login Data*'
        ]  # Collection of regex search filters to locate an artefact.
        self.icon = ''  # feathricon for report.

        self.debug_mode = True

    def _processor(self) -> bool:
    
        for file_found in self.files_found:
            file_found = str(file_found)
            if not os.path.basename(file_found) == 'Login Data': # skip -journal and other files
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
            username_value,
            password_value,
            CASE date_created 
                WHEN "0" THEN "" 
                ELSE datetime(date_created / 1000000 + (strftime('%s', '1601-01-01')), "unixepoch")
                END AS "date_created_win_epoch", 
            CASE date_created WHEN "0" THEN "" 
                ELSE datetime(date_created / 1000000 + (strftime('%s', '1970-01-01')), "unixepoch")
                END AS "date_created_unix_epoch",
            origin_url,
            blacklisted_by_user
            FROM logins
            ''')

            all_rows = cursor.fetchall()
            usageentries = len(all_rows)
            if usageentries > 0:
                data_headers = ('Created Time','Username','Password','Origin URL','Blacklisted by User')
                data_list = []
                for row in all_rows:
                    password = ''
                    password_enc = row[1]
                    if password_enc:
                        password = self.decrypt(password_enc).decode("utf-8", 'replace')
                    valid_date = self.get_valid_date(row[2], row[3])
                    data_list.append( (valid_date, row[0], password, row[4], row[5]) )

                artifact_report.GenerateHtmlReport(self, file_found, data_headers, data_list)

                tsvname = f'{browser_name} login data'
                tsv(self.report_folder, data_headers, data_list, tsvname)

                tlactivity = f'{browser_name} Login Data'
                timeline(self.report_folder, tlactivity, data_list, data_headers)
            else:
                logfunc(f'No {browser_name} Login Data available')

            db.close()

        return True

    def decrypt(self, ciphertxt, key = b"peanuts"):
        if re.match(rb"^v1[01]", ciphertxt):
            ciphertxt = ciphertxt[3:]
        salt = b"saltysalt"
        derived_key = PBKDF2(key, salt, 0x10, 1)
        iv = b" " * 0x10
        cipher = AES.new(derived_key, AES.MODE_CBC, IV = iv)
        try:
            plaintxt_pad = cipher.decrypt(ciphertxt)
            plaintxt = plaintxt_pad[:-ord(plaintxt_pad[len(plaintxt_pad) - 1:])]
        except ValueError as ex:
            logfunc('Exception while decrypting data: ' + str(ex))
            plaintxt = b''
        return plaintxt

    def get_valid_date(self, d1, d2):
        '''Returns a valid date based on closest year to now'''
        # Since the dates in question will be hundreds of years apart, this should be easy
        if d1 == '': return d2
        if d2 == '': return d1

        year1 = int(d1[0:4])
        year2 = int(d2[0:4])

        today = datetime.datetime.today()
        diff1 = abs(today.year - year1)
        diff2 = abs(today.year - year2)

        if diff1 < diff2:
            return d1
        else:
            return d2
