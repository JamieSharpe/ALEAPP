from scripts.ilapfuncs import timeline, open_sqlite_db_readonly

from scripts.plugin_base import ArtefactPlugin
from scripts.ilapfuncs import logfunc, tsv
from scripts import artifact_report

class VlcMediaPlugin(ArtefactPlugin):
    """
    """

    def __init__(self):
        super().__init__()
        self.author = 'Unknown'
        self.author_email = ''
        self.author_url = ''

        self.category = 'VLC'
        self.name = 'Media List'
        self.description = 'VLC Media List'

        self.artefact_reference = ''  # Description on what the artefact is.
        self.path_filters = ['*vlc_media.db*']  # Collection of regex search filters to locate an artefact.
        self.icon = 'film'  # feathricon for report.

    def _processor(self) -> bool:

        for file_found in self.files_found:
            file_found = str(file_found)

            if file_found.endswith('vlc_media.db'):
                break

        db = open_sqlite_db_readonly(file_found)
        cursor = db.cursor()
        cursor.execute('''
        SELECT
        datetime(insertion_date, 'unixepoch'),
        datetime(last_played_date,'unixepoch'),
        filename,
        path,
        is_favorite
        from Media
        left join Folder
        on Media.folder_id = Folder.id_folder
        ''')

        all_rows = cursor.fetchall()
        usageentries = len(all_rows)
        data_list = []

        if usageentries > 0:
            for row in all_rows:
                data_list.append((row[0], row[1], row[2], row[3], row[4]))

            data_headers = ('Insertion Date', 'Last Played Date', 'Filename', 'Path', 'Is Favorite?' )
            artifact_report.GenerateHtmlReport(self, file_found, data_headers, data_list)

            tsv(self.report_folder, data_headers, data_list, self.full_name())

            timeline(self.report_folder, self.full_name(), data_list, data_headers)
        else:
            logfunc('No VLC Media data available')

        db.close()

        return True


