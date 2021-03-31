from scripts.ilapfuncs import timeline, open_sqlite_db_readonly
from scripts.plugin_base import ArtefactPlugin
from scripts.ilapfuncs import logfunc, tsv
from scripts import artifact_report

class TikTokMessagesPlugin(ArtefactPlugin):
    """
    """

    def __init__(self):
        super().__init__()
        self.author = 'Unknown'
        self.author_email = ''
        self.author_url = ''

        self.category = 'TikTok'
        self.name = 'Messages'
        self.description = 'TikTok messages.'

        self.artefact_reference = ''  # Description on what the artefact is.
        self.path_filters = ['*_im.db*', '*db_im_xx*']  # Collection of regex search filters to locate an artefact.
        self.icon = 'message-square'  # feathricon for report.

    def _processor(self) -> bool:
        data_list = []

        for file_found in self.files_found:
            file_found = str(file_found)

            if file_found.endswith('_im.db'):
                maindb = file_found
            if file_found.endswith('db_im_xx'):
                attachdb = file_found

        db = open_sqlite_db_readonly(maindb)
        cursor = db.cursor()
        cursor.execute(f"ATTACH DATABASE '{attachdb}' as db_im_xx;")
        cursor.execute('''
            select
            datetime(created_time/1000, 'unixepoch', 'localtime') as created_time,
            UID,
            UNIQUE_ID,
            NICK_NAME,
            json_extract(content, '$.text') as message,
            json_extract(content,'$.display_name') as links_gifs_display_name,
            json_extract(content, '$.url.url_list[0]') as links_gifs_urls,
            read_status,
                case when read_status = 0 then 'Not read'
                    when read_status = 1 then 'Read'
                    else read_status
                end
            local_info
            from db_im_xx.SIMPLE_USER, msg
            where UID = sender order by created_time
            ''')

        all_rows = cursor.fetchall()

        if len(all_rows) > 0:
            for row in all_rows:

                data_list.append((row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7], row[8]))

            data_headers = ('Timestamp','UID','Unique ID','Nickname','Message','Link GIF Name','Link GIF URL','Read?','Local Info')
            artifact_report.GenerateHtmlReport(self, file_found, data_headers, data_list)

            tsv(self.report_folder, data_headers, data_list, self.full_name())

            timeline(self.report_folder, self.full_name(), data_list, data_headers)
        else:
            logfunc('No TikTok messages available')

        db.close()
