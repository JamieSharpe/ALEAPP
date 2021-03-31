from scripts.ilapfuncs import timeline, open_sqlite_db_readonly
from scripts.plugin_base import ArtefactPlugin
from scripts.artifact_report import ArtifactHtmlReport
from scripts.ilapfuncs import logfunc, tsv
from scripts import artifact_report

class CastPlugin(ArtefactPlugin):
    """
    """

    def __init__(self):
        super().__init__()
        self.author = 'Unknown'
        self.author_email = ''
        self.author_url = ''

        self.name = 'Cast'
        self.description = ''

        self.artefact_reference = ''  # Description on what the artefact is.
        self.path_filters = ['**/com.google.android.gms/databases/cast.db']  # Collection of regex search filters to locate an artefact.
        self.icon = ''  # feathricon for report.

    def _processor(self) -> bool:
    
        file_found = str(self.files_found[0])
        db = open_sqlite_db_readonly(file_found)
        cursor = db.cursor()
        cursor.execute('''
        SELECT
            device_id,
            capabilities,
            device_version,
            friendly_name,
            model_name,
            receiver_metrics_id,
            service_instance_name,
            service_address,
            service_port,
            supported_criteria,
            rcn_enabled_status,
            hotspot_bssid,
            cloud_devcie_id,
            case last_published_timestamp_millis
                when 0 then ''
                else datetime(last_published_timestamp_millis/1000, 'unixepoch')
            end as "Last Published Timestamp",
            case last_discovered_timestamp_millis
                when 0 then ''
                else datetime(last_discovered_timestamp_millis/1000, 'unixepoch')
            end as "Last Discovered Timestamp",
            case last_discovered_by_ble_timestamp_millis
                when 0 then ''
                else datetime(last_discovered_by_ble_timestamp_millis/1000, 'unixepoch')
            end as "Last Discovered By BLE Timestamp"
        from DeviceInfo
        ''')

        all_rows = cursor.fetchall()
        usageentries = len(all_rows)
        if usageentries > 0:
            data_headers = ('Device ID (SSDP UDN)','Capabilities','Device Version','Device Friendly Name','Device Model Name','Receiver Metrics ID','Service Instance Name','Device IP Address','Device Port','Supported Criteria','RCN Enabled Status','Hotspot BSSID','Cloud Device ID','Last Published Timestamp','Last Discovered Timestamp','Last Discovered By BLE Timestamp')
            data_list = []
            for row in all_rows:
                data_list.append((row[0],row[1],row[2],row[3],row[4],row[5],row[6],row[7],row[8],row[9],row[10],row[11],row[12],row[13],row[14],row[15]))

            artifact_report.GenerateHtmlReport(self, file_found, data_headers, data_list)

            tsv(self.report_folder, data_headers, data_list, self.full_name())

            timeline(self.report_folder, self.name, data_list, data_headers)
        else:
            logfunc('No Cast data available')

        db.close()
        return True
