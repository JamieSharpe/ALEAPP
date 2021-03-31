import xml.etree.ElementTree as ET

from scripts.plugin_base import ArtefactPlugin
from scripts.artifact_report import ArtifactHtmlReport
from scripts.ilapfuncs import logfunc, tsv
from scripts import artifact_report

class WiFiProfilesPlugin(ArtefactPlugin):
    """
    """

    def __init__(self):
        super().__init__()
        self.author = 'Unknown'
        self.author_email = ''
        self.author_url = ''

        self.name = 'WiFi Hotspots'
        self.description = ''

        self.artefact_reference = ''  # Description on what the artefact is.
        self.path_filters = [
            '**/misc/wifi/softap.conf',
            '**/misc**/apexdata/com.android.wifi/WifiConfigStoreSoftAp.xml'
        ]  # Collection of regex search filters to locate an artefact.
        self.icon = ''  # feathricon for report.

        self.debug_mode = True

    def _processor(self) -> bool:

        data_list = []
        for file_found in self.files_found:
            file_found = str(file_found)

            ssid = ''
            security_type = ''
            passphrase = ''

            if file_found.endswith('.conf'):
                with open(file_found, 'rb') as f:
                    data = f.read()
                    ssid_len = data[5]
                    ssid = data[6 : 6 + ssid_len].decode('utf8', 'ignore')

                    data_len = len(data)
                    start_pos = -1
                    while data[start_pos] != 0 and (-start_pos < data_len):
                        start_pos -= 1
                    passphrase = data[start_pos + 2:].decode('utf8', 'ignore')
            else:
                tree = ET.parse(file_found)
                for node in tree.iter('SoftAp'):
                    for elem in node.iter():
                        if not elem.tag==node.tag:
                            #print(elem.attrib)
                            data = elem.attrib
                            name = data.get('name', '')
                            if name == 'SSID':
                                ssid = elem.text
                            elif name == 'SecurityType':
                                security_type = data.get('value', '')
                            elif name == 'Passphrase':
                                passphrase = elem.text
            if ssid:
                data_list.append((ssid, passphrase, security_type))

        if data_list:
            data_headers = ('SSID', 'Passphrase', 'SecurityType')
            artifact_report.GenerateHtmlReport(self, file_found, data_headers, data_list)

            tsv(self.report_folder, data_headers, data_list, self.name)
        else:
            logfunc('No Wi-Fi Hotspot data available')
