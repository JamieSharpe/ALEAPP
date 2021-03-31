import xml.etree.ElementTree as ET 

from scripts.ilapfuncs import is_platform_windows
from scripts.plugin_base import ArtefactPlugin
from scripts.artifact_report import ArtifactHtmlReport
from scripts.ilapfuncs import logfunc, tsv
from scripts import artifact_report

class PermissionsPlugin(ArtefactPlugin):
    """
    """

    def __init__(self):
        super().__init__()
        self.author = 'Unknown'
        self.author_email = ''
        self.author_url = ''

        self.name = 'Permissions'
        self.description = ''

        self.artefact_reference = ''  # Description on what the artefact is.
        self.path_filters = ['*/system/packages.xml']  # Collection of regex search filters to locate an artefact.
        self.icon = ''  # feathricon for report.

    def _processor(self) -> bool:
    
        slash = '\\' if is_platform_windows() else '/'

        for file_found in self.files_found:
            file_found = str(file_found)

            data_list_permissions = []
            err = 0
            user = ''

            parts = file_found.split(slash)
            if 'mirror' in parts:
                user = 'mirror'

            if user == 'mirror':
                continue
            else:
                try:
                    ET.parse(file_found)
                except ET.ParseError:
                    logfunc('Parse error - Non XML file.')
                    err = 1

                if err == 0:
                    tree = ET.parse(file_found)
                    root = tree.getroot()

                    for elem in root:

                        if elem.tag == 'permissions':
                            for subelem in elem:
                                data_list_permissions.append((subelem.attrib.get('name', ''), subelem.attrib.get('package', ''), subelem.attrib.get('protection', '')))
                                #print(elem.tag +' '+ subelem.tag, subelem.attrib)

                    if len(data_list_permissions) > 0:

                        data_headers = ('Name', 'Package', 'Protection')
                        artifact_report.GenerateHtmlReport(self, file_found, data_headers, data_list_permissions)

                        tsv(self.report_folder, data_headers, data_list_permissions, self.name)

        return True
