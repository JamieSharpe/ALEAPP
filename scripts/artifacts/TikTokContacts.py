from scripts.ilapfuncs import timeline, open_sqlite_db_readonly
from scripts.plugin_base import ArtefactPlugin
from scripts.ilapfuncs import logfunc, tsv
from scripts import artifact_report

class TikTokContactsPlugin(ArtefactPlugin):
    """
    """

    def __init__(self):
        super().__init__()
        self.author = 'Unknown'
        self.author_email = ''
        self.author_url = ''

        self.category = 'TikTok'
        self.name = 'Contacts'
        self.description = 'TikTok contacts.'

        self.artefact_reference = ''  # Description on what the artefact is.
        self.path_filters = ['*_im.db*']  # Collection of regex search filters to locate an artefact.
        self.icon = 'user'  # feathricon for report.

    def _processor(self) -> bool:
        data_list = []

        for file_found in self.files_found:
            file_found = str(file_found)

            if file_found.endswith('_im.db'):
                maindb = file_found

        db = open_sqlite_db_readonly(maindb)
        cursor = db.cursor()
        cursor.execute('''
                    select
                    UID,
                    NICK_NAME,
                    UNIQUE_ID,
                    INITIAL_LETTER,
                    json_extract(AVATAR_THUMB, '$.url_list[0]') as avatarURL,
                    FOLLOW_STATUS 
                    from SIMPLE_USER
                    ''')

        all_rows = cursor.fetchall()

        if len(all_rows) > 0:
            for row in all_rows:
                data_list.append((row[0], row[1], row[2], row[3], row[4], row[5]))

            data_headers = ('UID', 'Nickname', 'Unique ID', 'Initial Letter', 'Avatar URL', 'Follow Status')
            artifact_report.GenerateHtmlReport(self, file_found, data_headers, data_list)

            tsv(self.report_folder, data_headers, data_list, self.full_name())

        else:
            logfunc('No TikTok Contacts available')

        db.close()

        return True
