import re
import xml.etree.ElementTree as ET

from scripts.ilapfuncs import is_platform_windows
from scripts.plugin_base import ArtefactPlugin
from scripts.artifact_report import ArtifactHtmlReport
from scripts.ilapfuncs import logfunc, tsv


class DeviceInfoPlugin(ArtefactPlugin):
    """
    """

    def __init__(self):
        super().__init__()
        self.author = 'Unknown'
        self.author_email = ''
        self.author_url = ''

        self.name = 'Device Info'
        self.description = ''

        self.artefact_reference = ''  # Description on what the artefact is.
        self.path_filters = ['**/system/users/*/settings_secure.xml']  # Collection of regex search filters to locate an artefact.
        self.icon = ''  # feathricon for report.

    def _processor(self) -> bool:

        slash = '\\' if is_platform_windows() else '/'
        # Filter for path xxx/yyy/system_ce/0
        for file_found in self.files_found:
            file_found = str(file_found)
            parts = file_found.split(slash)
            uid = parts[-2]
            try:
                uid_int = int(uid)
                # Skip sbin/.magisk/mirror/data/system_de/0 , it should be duplicate data??
                if file_found.find('{0}mirror{0}'.format(slash)) >= 0:
                    continue
                self.process_ssecure(file_found, uid)
            except ValueError:
                    pass # uid was not a number
        return True

    def process_ssecure(self, file_path, uid):

        try:
            tree = ET.parse(file_path)
            root = tree.getroot()
        except ET.ParseError: # Fix for android 11 invalid XML file (no root element present)
            with open(file_path) as f:
                xml = f.read()
                root = ET.fromstring(re.sub(r"(<\?xml[^>]+\?>)", r"\1<root>", xml) + "</root>")
        data_list = []
        for setting in root.iter('setting'):
            nme = setting.get('name')
            val = setting.get('value')
            if nme == 'bluetooth_name':
                data_list.append((nme, val))
            elif nme == 'mock_location':
                data_list.append((nme, val))
            elif nme == 'android_id':
                data_list.append((nme, val))
            elif nme == 'bluetooth_address':
                data_list.append((nme, val))

        if len(data_list) > 0:
            report = ArtifactHtmlReport('Settings Secure')
            report.start_artifact_report(self.report_folder, f'Settings_Secure_{uid}')
            report.add_script()
            data_headers = ('Name', 'Value')
            report.write_artifact_data_table(data_headers, data_list, file_path)
            report.end_artifact_report()

            tsvname = f'settings secure'
            tsv(self.report_folder, data_headers, data_list, tsvname)
        else:
            logfunc('No Settings Secure data available')

