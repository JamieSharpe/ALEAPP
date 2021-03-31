from scripts.ilapfuncs import open_sqlite_db_readonly
from scripts.plugin_base import ArtefactPlugin
from scripts.artifact_report import ArtifactHtmlReport
from scripts.ilapfuncs import logfunc, tsv


class ChessWithFriendsPlugin(ArtefactPlugin):
    """
    This plugin gets the build information.
    """

    def __init__(self):
        super().__init__()
        self.author = 'Unknown'
        self.author_email = ''
        self.author_url = ''

        self.name = 'Chats'
        self.description = ''

        self.artefact_reference = ''  # Description on what the artefact is.
        self.path_filters = [
            '**/com.zynga.chess.googleplay/databases/wf_database.sqlite',
            '**/com.zynga.chess.googleplay/db/wf_database.sqlite'
        ]  # Collection of regex search filters to locate an artefact.
        self.icon = ''  # feathricon for report.

    def _processor(self) -> bool:

        file_found = str(self.files_found[0])
        db = open_sqlite_db_readonly(file_found)
        cursor = db.cursor()
        cursor.execute('''
        SELECT
        chat_messages.chat_message_id,
        users.name,
        users.email_address,
        chat_messages.message,
        chat_messages.created_at
        FROM
        chat_messages
        INNER JOIN
        users
        ON
        chat_messages.user_id=users.user_id
        ORDER BY
        chat_messages.created_at DESC
        ''')

        all_rows = cursor.fetchall()
        usageentries = len(all_rows)
        if usageentries > 0:
            report = ArtifactHtmlReport('Chats')
            report.start_artifact_report(self.report_folder, 'Chess With Friends')
            report.add_script()
            data_headers = ('Message_ID','User_Name','User_Email','Chat_Message','Chat_Message_Creation' )
            data_list = []
            for row in all_rows:
                data_list.append((row[0],row[1],row[2],row[3],row[4]))

            report.write_artifact_data_table(data_headers, data_list, file_found)
            report.end_artifact_report()

            tsvname = f'Chess With Friends Chats'
            tsv(self.report_folder, data_headers, data_list, tsvname)
        else:
            logfunc('No Chess With Friends data available')

        db.close()
        return True

