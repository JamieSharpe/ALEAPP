import xml.etree.ElementTree as ET 

from scripts.ilapfuncs import is_platform_windows
from scripts.plugin_base import ArtefactPlugin
from scripts.artifact_report import ArtifactHtmlReport
from scripts.ilapfuncs import tsv
from scripts import artifact_report

class AppRolesPlugin(ArtefactPlugin):
    """
    """

    def __init__(self):
        super().__init__()
        self.author = 'Unknown'
        self.author_email = ''
        self.author_url = ''

        self.name = 'App Roles'
        self.description = ''

        self.artefact_reference = ''  # Description on what the artefact is.
        self.path_filters = [
            '*/system/users/*/roles.xml',
            '*/misc_de/*/apexdata/com.android.permission/roles.xml'
        ]  # Collection of regex search filters to locate an artefact.
        self.icon = ''  # feathricon for report.

    def _processor(self) -> bool:
    
        run = 0
        slash = '\\' if is_platform_windows() else '/'

        for file_found in self.files_found:
            file_found = str(file_found)

            data_list = []
            run = run + 1
            err = 0


            parts = file_found.split(slash)
            if 'mirror' in parts:
                user = 'mirror'
            elif 'users' in parts:
                user = parts[-2]
                ver = 'Android 10'
            elif 'misc_de' in parts:
                user = parts[-4]
                ver = 'Android 11'

            if user == 'mirror':
                continue
            else:
                try:
                    ET.parse(file_found)
                except ET.ParseError:
                    print('Parse error - Non XML file.') #change to logfunc
                    err = 1

                if err == 0:
                    tree = ET.parse(file_found)
                    root = tree.getroot()

                    for elem in root:
                        holder = ''
                        role = elem.attrib['name']
                        for subelem in elem:
                            holder = subelem.attrib['name']

                        data_list.append((role, holder))

                    if len(data_list) > 0:
                        data_headers = ('Role', 'Holder')
                        artifact_report.GenerateHtmlReport(self, file_found, data_headers, data_list)

                        tsvname = f'App Roles_{user}'
                        tsv(self.report_folder, data_headers, data_list, tsvname)

        return True
