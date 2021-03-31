from scripts.ilapfuncs import logfunc, tsv, timeline, is_platform_windows, get_next_unused_name, open_sqlite_db_readonly
from scripts.plugin_base import ArtefactPlugin
from scripts.artifact_report import ArtifactHtmlReport
from scripts.ilapfuncs import logfunc, tsv
from scripts import artifact_report


class FacebookMessengerContactsPlugin(ArtefactPlugin):
    """
    """

    def __init__(self):
        super().__init__()
        self.author = 'Unknown'
        self.author_email = ''
        self.author_url = ''

        self.category = 'Facebook'
        self.name = 'Contacts'
        self.description = 'Facebook messenger contacts'

        self.artefact_reference = ''  # Description on what the artefact is.
        self.path_filters = ['*/threads_db2*']  # Collection of regex search filters to locate an artefact.
        self.icon = 'facebook'  # feathricon for report.

    def _processor(self) -> bool:
    
        for file_found in self.files_found:

            if not file_found.endswith('threads_db2'):
                continue # Skip all other files

            db = open_sqlite_db_readonly(file_found)
            cursor = db.cursor()
            cursor.execute('''
            select
            substr(user_key,10),
            first_name,
            last_name,
            username,
            (select json_extract (profile_pic_square, '$[0].url')) as profile_pic_square,
            case is_messenger_user
                when 0 then ''
                else 'Yes'
            end is_messenger_user,
            case is_friend
                when 0 then 'No'
                else 'Yes'
            end is_friend
            from thread_users
            ''')

            all_rows = cursor.fetchall()
            usageentries = len(all_rows)
            if usageentries > 0:
                data_headers = ('User ID','First Name','Last Name','Username','Profile Pic URL','Is App User','Is Friend') # Don't remove the comma, that is required to make this a tuple as there is only 1 element
                data_list = []
                for row in all_rows:
                    data_list.append((row[0],row[1],row[2],row[3],row[4],row[5],row[6]))

                artifact_report.GenerateHtmlReport(self, file_found, data_headers, data_list)

                tsv(self.report_folder, data_headers, data_list, self.full_name())

                timeline(self.report_folder, self.full_name(), data_list, data_headers)
            else:
                logfunc('No Facebook Messenger - Contacts data not available')

            db.close()
        return True
