from scripts.ilapfuncs import timeline, open_sqlite_db_readonly

from scripts.plugin_base import ArtefactPlugin
from scripts.artifact_report import ArtifactHtmlReport
from scripts.ilapfuncs import logfunc, tsv


class InstalledAppsVendingPlugin(ArtefactPlugin):
    """
    """

    def __init__(self):
        super().__init__()
        self.author = 'Unknown'
        self.author_email = ''
        self.author_url = ''

        self.name = 'Installed Apps'
        self.description = ''

        self.artefact_reference = ''  # Description on what the artefact is.
        self.path_filters = ['**/com.android.vending/databases/localappstate.db']  # Collection of regex search filters to locate an artefact.
        self.icon = ''  # feathricon for report.

    def _processor(self) -> bool:

        file_found = str(self.files_found[0])
        db = open_sqlite_db_readonly(file_found)
        cursor = db.cursor()
        cursor.execute('''
        SELECT
            CASE
                first_download_ms
                WHEN
                    "0" 
                THEN
                    "0" 
                ELSE
                    datetime(first_download_ms / 1000, "unixepoch")
            END AS "fdl",
            package_name,
            title,
            install_reason,
            auto_update
        FROM appstate  
        ''')

        all_rows = cursor.fetchall()
        usageentries = len(all_rows)
        if usageentries > 0:
            report = ArtifactHtmlReport('Installed Apps (Vending)')
            report.start_artifact_report(self.report_folder, 'Installed Apps (Vending)')
            report.add_script()
            data_headers = ('First Download','Package Name', 'Title','Install Reason', 'Auto Update?')
            data_list = []
            for row in all_rows:
                data_list.append((row[0], row[1], row[2], row[3], row[4]))

            report.write_artifact_data_table(data_headers, data_list, file_found)
            report.end_artifact_report()

            tsvname = f'installed apps vending'
            tsv(self.report_folder, data_headers, data_list, tsvname)

            tlactivity = f'Installed Apps Vending'
            timeline(self.report_folder, tlactivity, data_list, data_headers)
        else:
                logfunc('No Installed Apps data available')

        db.close()

        return True
