from scripts.plugin_base import ArtefactPlugin
from scripts.artifact_report import ArtifactHtmlReport
from scripts.ilapfuncs import logfunc, tsv
from scripts import artifact_report

class AdbHostsPlugin(ArtefactPlugin):
    """
    """

    def __init__(self):
        super().__init__()
        self.author = 'Unknown'
        self.author_email = ''
        self.author_url = ''

        self.name = 'ADB Hosts'
        self.description = ''

        self.artefact_reference = ''  # Description on what the artefact is.
        self.path_filters = ['**/data/misc/adb/adb_keys']  # Collection of regex search filters to locate an artefact.
        self.icon = ''  # feathricon for report.

    def _processor(self) -> bool:
        data_list = []
        file_found = str(self.files_found[0])

        with open(file_found, 'r') as f:
            user_and_host_list = [line.split(" ")[1].rstrip('\n').split('@', 1) for line in f]
            data_list = user_and_host_list

        if len(data_list) > 0:
            data_headers = ('Username', 'Hostname')
            artifact_report.GenerateHtmlReport(self, file_found, data_headers, data_list)

            tsv(self.report_folder, data_headers, data_list, self.name)

        else:
            logfunc(f'No ADB Hosts file available')

        return True
