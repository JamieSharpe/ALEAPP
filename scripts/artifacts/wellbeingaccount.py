import json

from scripts.parse3 import ParseProto
from scripts.plugin_base import ArtefactPlugin
from scripts.artifact_report import ArtifactHtmlReport
from scripts.ilapfuncs import tsv
from scripts import artifact_report

class WellBeingAccountPlugin(ArtefactPlugin):
    """
    """

    def __init__(self):
        super().__init__()
        self.author = 'Unknown'
        self.author_email = ''
        self.author_url = ''

        self.category = 'Wellbeing'
        self.name = 'Account'
        self.description = ''

        self.artefact_reference = ''  # Description on what the artefact is.
        self.path_filters = ['**/com.google.android.apps.wellbeing/files/AccountData.pb']  # Collection of regex search filters to locate an artefact.
        self.icon = 'user'  # feathricon for report.

    def _processor(self) -> bool:

        file_found = str(self.files_found[0])
        content = ParseProto(file_found)

        content_json_dump = json.dumps(content, indent=4, sort_keys=True, ensure_ascii=False)
        parsedContent = str(content_json_dump).encode(encoding='UTF-8', errors='ignore')

        data_headers = ('Protobuf Parsed Data', 'Protobuf Data')
        data_list = []
        data_list.append(('<pre id=\"json\">'+str(parsedContent).replace("\\n", "<br>")+'</pre>', str(content)))
        artifact_report.GenerateHtmlReport(self, file_found, data_headers, data_list, allow_html = True)

        tsv(self.report_folder, data_headers, data_list, self.full_name())

        return True
