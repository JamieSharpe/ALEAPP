import codecs
from scripts.plugin_base import ArtefactPlugin
from scripts.artifact_report import ArtifactHtmlReport
from scripts.ilapfuncs import logfunc, tsv
from scripts import artifact_report

class EtcHostsPlugin(ArtefactPlugin):
    """
    """

    def __init__(self):
        super().__init__()
        self.author = 'Unknown'
        self.author_email = ''
        self.author_url = ''

        self.name = 'Etc Hosts'
        self.description = ''

        self.artefact_reference = ''  # Description on what the artefact is.
        self.path_filters = ['**/system/etc/hosts']  # Collection of regex search filters to locate an artefact.
        self.icon = ''  # feathricon for report.

    def _processor(self) -> bool:
        data_list = []
        file_found = str(self.files_found[0])

        with codecs.open(file_found, 'r', 'utf-8-sig') as csvfile:
            for row in csvfile:
                sline = '\t'.join(row.split())
                sline = sline.split('\t')
                sline_one = sline[0]
                sline_two = sline[1]
                if (sline_one == '127.0.0.1' and sline_two == 'localhost') or \
                    (sline_one == '::1' and sline_two == 'ip6-localhost'):
                    pass # Skipping the defaults, so only anomaly entries are seen
                else:
                     data_list.append((sline_one, sline_two))

        if len(data_list) > 0:
            data_headers = ('IP Address', 'Hostname')
            artifact_report.GenerateHtmlReport(self, file_found, data_headers, data_list)

            tsvname = f'Etc Hosts'
            tsv(self.report_folder, data_headers, data_list, tsvname)

        else:
            logfunc(f'No etc hosts file available, or nothing significant found.')

        return True
