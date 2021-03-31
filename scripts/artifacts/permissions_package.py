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

        self.name = 'Permissions - Package and Shared User'
        self.description = ''

        self.artefact_reference = ''  # Description on what the artefact is.
        self.path_filters = ['*/system/packages.xml']  # Collection of regex search filters to locate an artefact.
        self.icon = ''  # feathricon for report.

        self.debug_mode = True

    def _processor(self) -> bool:
    
        slash = '\\' if is_platform_windows() else '/'

        for file_found in self.files_found:
            file_found = str(file_found)

            data_list_packages_su = []
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
                        if not elem.tag == 'permissions' and not elem.tag == 'permission-trees':
                            for subelem in elem:
                                if subelem.tag == 'perms':
                                    for sub_subelem in subelem:
                                        #print(elem.tag, elem.attrib['name'], sub_subelem.attrib['name'], sub_subelem.attrib['granted'] )
                                        data_list_packages_su.append((elem.tag, elem.attrib.get('name', ''), sub_subelem.attrib.get('name', ''), sub_subelem.attrib.get('granted', '')))

                    if len(data_list_packages_su) > 0:
                        report = ArtifactHtmlReport('Package and Shared User')
                        report.start_artifact_report(self.report_folder, f'Package and Shared User')
                        report.add_script()
                        data_headers = ('Type', 'Package', 'Permission', 'Granted?')
                        artifact_report.GenerateHtmlReport(self, file_found, data_headers, data_list_packages_su)

                        tsv(self.report_folder, data_headers, data_list_packages_su, self.name)

        return True
