from scripts.ilapfuncs import is_platform_windows, open_sqlite_db_readonly
from scripts.plugin_base import ArtefactPlugin
from scripts.artifact_report import ArtifactHtmlReport
from scripts.ilapfuncs import logfunc, tsv


class SimInfoPlugin(ArtefactPlugin):
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
        self.path_filters = ['**/user_de/*/com.android.providers.telephony/databases/telephony.db']  # Collection of regex search filters to locate an artefact.
        self.icon = ''  # feathricon for report.

    def _processor(self) -> bool:

        slash = '\\' if is_platform_windows() else '/'
        # Filter for path xxx/yyy/system_ce/0
        for file_found in self.files_found:
            file_found = str(file_found)
            parts = file_found.split(slash)
            uid = parts[-4]
            try:
                uid_int = int(uid)
                # Skip sbin/.magisk/mirror/data/system_de/0 , it should be duplicate data??
                if file_found.find('{0}mirror{0}'.format(slash)) >= 0:
                    continue
                self.process_siminfo(file_found, uid)
            except ValueError:
                pass # uid was not a number

        return True

    def process_siminfo(self, folder, uid):

        #Query to create report
        db = open_sqlite_db_readonly(folder)
        cursor = db.cursor()

        #Query to create report
        try:
            cursor.execute('''
            SELECT
                number,
                imsi,
                display_name,
                carrier_name,
                iso_country_code,
                carrier_id,
                icc_id
            FROM
                siminfo
            ''')
        except:
            cursor.execute('''
            SELECT
                number,
                card_id,
                display_name,
                carrier_name,
                carrier_name,
                carrier_name,
                icc_id
            FROM
                siminfo
            ''')

        all_rows = cursor.fetchall()
        usageentries = len(all_rows)
        if usageentries > 0:
            report = ArtifactHtmlReport('Device Info')
            report.start_artifact_report(self.report_folder, f'SIM_info_{uid}')
            report.add_script()
            data_headers = ('Number', 'IMSI', 'Display Name','Carrier Name', 'ISO Code', 'Carrier ID', 'ICC ID')

            data_list = []
            for row in all_rows:
                if row[3] == row[4]:
                    row1 = ''
                    row4 = ''
                    row5 = ''
                else:
                    row1 = row[1]
                    row4 = row[4]
                    row5 = row[5]
                data_list.append((row[0], row1, row[2], row[3], row4, row5, row[6]))
            report.write_artifact_data_table(data_headers, data_list, folder)
            report.end_artifact_report()

            tsvname = f'sim info {uid}'
            tsv(self.report_folder, data_headers, data_list, tsvname)
        else:
            logfunc(f'No SIM_Info{uid} data available')
        db.close()
