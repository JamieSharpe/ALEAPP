from scripts.ilapfuncs import logfunc, tsv, timeline, is_platform_windows, get_next_unused_name, open_sqlite_db_readonly
from scripts.plugin_base import ArtefactPlugin
from scripts.artifact_report import ArtifactHtmlReport
from scripts.ilapfuncs import logfunc, tsv
from scripts import artifact_report


class FacebookMessengerChatsPlugin(ArtefactPlugin):
    """
    """

    def __init__(self):
        super().__init__()
        self.author = 'Unknown'
        self.author_email = ''
        self.author_url = ''

        self.category = 'Facebook'
        self.name = 'Chats'
        self.description = 'Facebook messenger chats'

        self.artefact_reference = ''  # Description on what the artefact is.
        self.path_filters = ['**/threads_db2*']  # Collection of regex search filters to locate an artefact.
        self.icon = 'facebook'  # feathricon for report.

    def _processor(self) -> bool:
    
        for file_found in self.files_found:

            if not file_found.endswith('threads_db2'):
                continue # Skip all other files

            db = open_sqlite_db_readonly(file_found)
            cursor = db.cursor()
            cursor.execute('''
            select
            case messages.timestamp_ms
                when 0 then ''
                else datetime(messages.timestamp_ms/1000,'unixepoch')
            End	as Datestamp,
            (select json_extract (messages.sender, '$.name')) as "Sender",
            substr((select json_extract (messages.sender, '$.user_key')),10) as "Sender ID",
            messages.thread_key,
            messages.text,
            messages.snippet,
            (select json_extract (messages.attachments, '$[0].filename')) as AttachmentName,
            --messages.attachments,
            --messages.shares,
            (select json_extract (messages.shares, '$[0].name')) as ShareName,
            (select json_extract (messages.shares, '$[0].description')) as ShareDesc,
            (select json_extract (messages.shares, '$[0].href')) as ShareLink
            from messages, threads
            where messages.thread_key=threads.thread_key and generic_admin_message_extensible_data IS NULL and msg_type != -1
            order by messages.thread_key, datestamp;
            ''')

            all_rows = cursor.fetchall()
            usageentries = len(all_rows)
            if usageentries > 0:
                data_headers = ('Timestamp','Sender Name','Sender ID','Thread Key','Message','Snippet','Attachment Name','Share Name','Share Description','Share Link') # Don't remove the comma, that is required to make this a tuple as there is only 1 element
                data_list = []
                for row in all_rows:
                    data_list.append((row[0],row[1],row[2],row[3],row[4],row[5],row[6],row[7],row[8],row[9]))

                artifact_report.GenerateHtmlReport(self, file_found, data_headers, data_list)

                tsv(self.report_folder, data_headers, data_list, self.full_name())

                timeline(self.report_folder, self.full_name(), data_list, data_headers)
            else:
                logfunc('No Facebook Messenger - Chats data not available')

            db.close()

        return True
