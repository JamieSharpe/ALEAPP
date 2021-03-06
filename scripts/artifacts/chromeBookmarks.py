import datetime
import json
import os

from scripts.ilapfuncs import timeline, get_next_unused_name
from scripts.plugin_base import ArtefactPlugin
from scripts.artifact_report import ArtifactHtmlReport
from scripts.ilapfuncs import logfunc, tsv
from scripts import artifact_report

class ChromeBookmarksPlugin(ArtefactPlugin):
    """
    """

    def __init__(self):
        super().__init__()
        self.author = 'Unknown'
        self.author_email = ''
        self.author_url = ''

        self.category = 'Chromium'
        self.name = 'Bookmarks'
        self.description = ''

        self.artefact_reference = ''  # Description on what the artefact is.
        self.path_filters = [
            '**/app_chrome/Default/Bookmarks*',
            '**/app_sbrowser/Default/Bookmarks*',
            '**/app_opera/Bookmarks*'
        ]  # Collection of regex search filters to locate an artefact.
        self.icon = 'bookmark'  # feathricon for report.

    def _processor(self) -> bool:

        for file_found in self.files_found:
            file_found = str(file_found)
            if not os.path.basename(file_found) == 'Bookmarks': # skip -journal and other files
                continue
            elif file_found.find('.magisk') >= 0 and file_found.find('mirror') >= 0:
                continue # Skip sbin/.magisk/mirror/data/.. , it should be duplicate data??
            browser_name = self.get_browser_name(file_found)
            if file_found.find('app_sbrowser') >= 0:
                browser_name = 'Browser'

            with open(file_found, "r") as f:
                dataa = json.load(f)
            data_list = []
            for x, y in dataa.items():
                flag = 0
                if isinstance(y,dict):
                    for key, value in y.items():
                        if isinstance(value,dict):
                            for keyb, valueb in value.items():
                                if keyb == 'children':
                                    if len(valueb) > 0:
                                        url = valueb[0]['url']
                                        dateadd = valueb[0]['date_added']
                                        dateaddconv = datetime.datetime(1601, 1, 1) + datetime.timedelta(microseconds=int(dateadd))
                                        name = valueb[0]['name']
                                        typed = valueb[0]['type']
                                        flag = 1
                                if keyb == 'name' and flag == 1:
                                    flag = 0
                                    parent = valueb
                                    data_list.append((dateaddconv, url, name, parent, typed))
            num_entries = len(data_list)
            if num_entries > 0:
                data_headers = ('Added Date', 'URL', 'Name', 'Parent', 'Type')
                artifact_report.GenerateHtmlReport(self, file_found, data_headers, data_list)

                tsv(self.report_folder, data_headers, data_list, self.full_name())

                timeline(self.report_folder, self.name, data_list, data_headers)
            else:
                logfunc('No Browser Bookmarks data available')

        return True

    def get_browser_name(self, file_name):

        if 'microsoft' in file_name.lower():
            return 'Edge'
        elif 'chrome' in file_name.lower():
            return 'Chrome'
        elif 'opera' in file_name.lower():
            return 'Opera'
        else:
            return 'Unknown'
