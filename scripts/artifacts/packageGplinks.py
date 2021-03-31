from scripts.plugin_base import ArtefactPlugin
from scripts.ilapfuncs import logfunc, tsv
from scripts import artifact_report


class PackageGplinksPlugin(ArtefactPlugin):
    """
    """

    def __init__(self):
        super().__init__()
        self.author = 'Unknown'
        self.author_email = ''
        self.author_url = ''

        self.category = 'Google Play'
        self.name = 'Links for Apps'
        self.description = ''

        self.artefact_reference = ''  # Description on what the artefact is.
        self.path_filters = ['*/system/packages.list']  # Collection of regex search filters to locate an artefact.
        self.icon = 'package'  # feathricon for report.

    def _processor(self) -> bool:
        data_list = []

        for file_found in self.files_found:
            if 'sbin' not in file_found:
                file_found = str(file_found)
                source_file = file_found.replace(self.seeker.directory, '')

            with open(file_found) as data:
                values = data.readlines()

            for x in values:
                bundleid = x.split(' ', 1)
                url = f'<a href="https://play.google.com/store/apps/details?id={bundleid[0]}" target="_blank"><font color="blue">https://play.google.com/store/apps/details?id={bundleid[0]}</font></a>'
                data_list.append((bundleid[0], url))

            usageentries = len(data_list)
            if usageentries > 0:
                data_headers = ('Bundle ID', 'Possible Google Play Store Link')

                artifact_report.GenerateHtmlReport(self, file_found, data_headers, data_list, allow_html = True)

                tsv(self.report_folder, data_headers, data_list, self.full_name(), source_file)

            else:
                logfunc('No Google Play Links for Apps data available')

        return True
