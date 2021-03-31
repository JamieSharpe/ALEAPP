from scripts.plugin_base import ArtefactPlugin
from scripts.artifact_report import ArtifactHtmlReport
from scripts.ilapfuncs import logfunc, tsv


class Plugin(ArtefactPlugin):
    """
    This plugin gets the build information.
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
            report = ArtifactHtmlReport('ADB Hosts')
            report.start_artifact_report(self.report_folder, f'ADB Hosts')
            report.add_script()
            data_headers = ('Username', 'Hostname')
            report.write_artifact_data_table(data_headers, data_list, file_found)
            report.end_artifact_report()

            tsvname = f'ADB Hosts'
            tsv(self.report_folder, data_headers, data_list, tsvname)

        else:
            logfunc(f'No ADB Hosts file available')

        return True
