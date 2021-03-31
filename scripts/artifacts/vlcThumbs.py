import os
import shutil

from scripts.plugin_base import ArtefactPlugin
from scripts.ilapfuncs import tsv
from scripts import artifact_report

class VlcThumbsPlugin(ArtefactPlugin):
    """
    """

    def __init__(self):
        super().__init__()
        self.author = 'Unknown'
        self.author_email = ''
        self.author_url = ''

        self.category = 'VLC'
        self.name = 'Thumbnails'
        self.description = 'VLC thumbnail icons.'

        self.artefact_reference = ''  # Description on what the artefact is.
        self.path_filters = ['*/org.videolan.vlc/files/medialib/*.jpg']  # Collection of regex search filters to locate an artefact.
        self.icon = 'image'  # feathricon for report.

    def _processor(self) -> bool:

        data_list = []
        for file_found in self.files_found:

            data_file_real_path = file_found
            shutil.copy2(data_file_real_path, self.report_folder)
            data_file_name = os.path.basename(data_file_real_path)
            thumb = f'<img src="{self.report_folder}/{data_file_name}"></img>'

            data_list.append((data_file_name, thumb))

        path_to_files = os.path.dirname(file_found)
        data_headers = ('Filename', 'Thumbnail')
        artifact_report.GenerateHtmlReport(self, path_to_files, data_headers, data_list)

        tsv(self.report_folder, data_headers, data_list, self.full_name())
