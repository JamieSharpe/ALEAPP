from scripts.ilapfuncs import logfunc, tsv, timeline, is_platform_windows, get_next_unused_name, open_sqlite_db_readonly
from scripts.plugin_base import ArtefactPlugin
from scripts.artifact_report import ArtifactHtmlReport
from scripts.ilapfuncs import logfunc, tsv
from scripts import artifact_report


class FacebookMessengerCallsPlugin(ArtefactPlugin):
    """
    """

    def __init__(self):
        super().__init__()
        self.author = 'Unknown'
        self.author_email = ''
        self.author_url = ''

        self.category = 'Facebook'
        self.name = 'Calls'
        self.description = 'Facebook messenger calls'

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
            datetime((messages.timestamp_ms/1000)-(select json_extract (messages.generic_admin_message_extensible_data, '$.call_duration')),'unixepoch') as "Timestamp",
            (select json_extract (messages.generic_admin_message_extensible_data, '$.caller_id')) as "Caller ID",
            (select json_extract (messages.sender, '$.name')) as "Receiver",
            substr((select json_extract (messages.sender, '$.user_key')),10) as "Receiver ID",
            --messages.generic_admin_message_extensible_data,
            strftime('%H:%M:%S',(select json_extract (messages.generic_admin_message_extensible_data, '$.call_duration')), 'unixepoch')as "Call Duration",
            case (select json_extract (messages.generic_admin_message_extensible_data, '$.video'))
                when false then ''
                else 'Yes'
            End as "Video Call"
            from messages, threads
            where messages.thread_key=threads.thread_key and generic_admin_message_extensible_data NOT NULL
            order by messages.thread_key, "Date/Time End";
            ''')

            all_rows = cursor.fetchall()
            usageentries = len(all_rows)
            if usageentries > 0:
                data_headers = ('Timestamp','Caller ID','Receiver Name','Receiver ID','Call Duration','Video Call') # Don't remove the comma, that is required to make this a tuple as there is only 1 element
                data_list = []
                for row in all_rows:
                    data_list.append((row[0],row[1],row[2],row[3],row[4],row[5]))

                artifact_report.GenerateHtmlReport(self, file_found, data_headers, data_list)

                tsv(self.report_folder, data_headers, data_list, self.full_name())

                timeline(self.report_folder, self.full_name(), data_list, data_headers)
            else:
                logfunc('No Facebook Messenger - Calls data not available')

            db.close()

        return True
