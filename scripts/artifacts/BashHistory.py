import codecs
from scripts.plugin_base import ArtefactPlugin
from scripts.artifact_report import ArtifactHtmlReport
from scripts.ilapfuncs import logfunc, tsv
from scripts import artifact_report

class BashHistoryPlugin(ArtefactPlugin):
    """
    """

    def __init__(self):
        super().__init__()
        self.author = 'Unknown'
        self.author_email = ''
        self.author_url = ''

        self.name = 'Bash History'
        self.description = ''

        self.artefact_reference = ''  # Description on what the artefact is.
        self.path_filters = ['**/.bash_history']  # Collection of regex search filters to locate an artefact.
        self.icon = ''  # feathricon for report.

        self.debug_mode = False

    def _processor(self) -> bool:
        data_list = []
        file_found = str(self.files_found[0])
        counter = 1
        with codecs.open(file_found, 'r', 'utf-8-sig') as csvfile:
            for row in csvfile:
                data_list.append((counter, row))
                counter += 1

        if len(data_list) > 0:
            data_headers = ('Order', 'Command')
            artifact_report.GenerateHtmlReport(self, file_found, data_headers, data_list)

            tsvname = f'Bash History'
            tsv(self.report_folder, data_headers, data_list, tsvname)

        else:
            logfunc(f'No Bash History file available')

        return True
