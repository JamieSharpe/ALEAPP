from scripts.ilapfuncs import logfunc, tsv, timeline, open_sqlite_db_readonly
from scripts.plugin_base import ArtefactPlugin
from scripts.artifact_report import ArtifactHtmlReport
from scripts.ilapfuncs import logfunc, tsv


class WordsWithFriendsPlugin(ArtefactPlugin):
    """
    """

    def __init__(self):
        super().__init__()
        self.author = 'Unknown'
        self.author_email = ''
        self.author_url = ''

        self.name = 'Chats'
        self.description = ''

        self.artefact_reference = ''  # Description on what the artefact is.
        self.path_filters = ['**/com.zynga.words/db/wf_database.sqlite']  # Collection of regex search filters to locate an artefact.
        self.icon = ''  # feathricon for report.

    def _processor(self) -> bool:

        file_found = str(self.files_found[0])
        db = open_sqlite_db_readonly(file_found)
        cursor = db.cursor()
        cursor.execute('''
        SELECT
        datetime(messages.created_at/1000, 'unixepoch'),
        messages.conv_id,
        users.name,
        users.email_address,
        messages.text
        FROM
        messages
        INNER JOIN
        users
        ON
        messages.user_zynga_id=users.zynga_account_id
        ORDER BY
        messages.created_at DESC
        ''')

        all_rows = cursor.fetchall()
        usageentries = len(all_rows)
        if usageentries > 0:
            report = ArtifactHtmlReport('Chats')
            report.start_artifact_report(self.report_folder, 'Words With Friends')
            report.add_script()
            data_headers = ('Chat_Message_Creation','Message_ID','User_Name','User_Email','Chat_Message' ) # Don't remove the comma, that is required to make this a tuple as there is only 1 element
            data_list = []
            for row in all_rows:
                data_list.append((row[0],row[1],row[2],row[3],row[4]))

            report.write_artifact_data_table(data_headers, data_list, file_found)
            report.end_artifact_report()

            tsvname = f'Words With Friends Chats'
            tsv(self.report_folder, data_headers, data_list, tsvname)

            tlactivity = f'Words with Friends Chats'
            timeline(self.report_folder, tlactivity, data_list, data_headers)
        else:
            logfunc('No Words With Friends data available')

        db.close()
        return True
