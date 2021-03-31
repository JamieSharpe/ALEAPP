import os
from scripts.ilapfuncs import timeline, get_next_unused_name, open_sqlite_db_readonly
from scripts.plugin_base import ArtefactPlugin
from scripts.artifact_report import ArtifactHtmlReport
from scripts.ilapfuncs import logfunc, tsv
from scripts import artifact_report

class ChromeMediaHistoryPlaybacksPlugin(ArtefactPlugin):
    """
    """

    def __init__(self):
        super().__init__()
        self.author = 'Unknown'
        self.author_email = ''
        self.author_url = ''

        self.category = 'Chrome'
        self.name = 'Media History - Playbacks'
        self.description = ''

        self.artefact_reference = ''  # Description on what the artefact is.
        self.path_filters = [
            '**/app_chrome/Default/Media History*',
             '**/app_sbrowser/Default/Media History*'
        ]  # Collection of regex search filters to locate an artefact.
        self.icon = ''  # feathricon for report.

        self.debug_mode = True

    def _processor(self) -> bool:

        for file_found in self.files_found:
            file_found = str(file_found)
            if not file_found.endswith('Media History'):
                continue  # Skip all other files

            elif file_found.find('.magisk') >= 0 and file_found.find('mirror') >= 0:
                continue  # Skip sbin/.magisk/mirror/data/.. , it should be duplicate data??

            db = open_sqlite_db_readonly(file_found)
            cursor = db.cursor()
            cursor.execute('''
                        select
                            datetime(last_updated_time_s-11644473600, 'unixepoch') as last_updated_time_s,
                            id,
                            origin_id,
                            url,
                            strftime('%H:%M:%S',watch_time_s, 'unixepoch') as watch_time_s,
                            case has_audio
                                when 0 then ''
                                when 1 then 'Yes'
                            end as has_audio,
                            case has_video
                                when 0 then ''
                                when 1 then 'Yes'
                            end as has_video  
                        from playback
                        ''')

            all_rows = cursor.fetchall()
            usageentries = len(all_rows)
            if usageentries > 0:
                data_headers = ('Last Updated', 'ID', 'Origin ID', 'URL', 'Watch Time', 'Has Audio',
                                'Has Video')  # Don't remove the comma, that is required to make this a tuple as there is only 1 element
                data_list = []
                for row in all_rows:
                    data_list.append((row[0], row[1], row[2], row[3], row[4], row[5], row[6]))

                artifact_report.GenerateHtmlReport(self, file_found, data_headers, data_list)

                tsv(self.report_folder, data_headers, data_list, self.name)

                timeline(self.report_folder, self.name, data_list, data_headers)
            else:
                logfunc('No Browser Media History - Playbacks data available')
