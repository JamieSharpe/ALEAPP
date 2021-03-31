from scripts.ilapfuncs import timeline, open_sqlite_db_readonly
from scripts.plugin_base import ArtefactPlugin
from scripts.artifact_report import ArtifactHtmlReport
from scripts.ilapfuncs import logfunc, tsv


class WellbeingUrlsPlugin(ArtefactPlugin):
    """
    """

    def __init__(self):
        super().__init__()
        self.author = 'Unknown'
        self.author_email = ''
        self.author_url = ''

        self.name = 'Wellbeing'
        self.description = ''

        self.artefact_reference = ''  # Description on what the artefact is.
        self.path_filters = ['**/com.google.android.apps.wellbeing/databases/app_usage*']  # Collection of regex search filters to locate an artefact.
        self.icon = ''  # feathricon for report.

    def _processor(self) -> bool:

        for file_found in self.files_found:
            file_found = str(file_found)
            if not file_found.endswith('app_usage'):
                continue # Skip all other files

            db = open_sqlite_db_readonly(file_found)
            cursor = db.cursor()
            cursor.execute('''
            SELECT 
            datetime(component_events.timestamp/1000, "UNIXEPOCH") as timestamp,
            component_events._id,
            components.package_id, 
            packages.package_name, 
            components.component_name as website,
            CASE
            when component_events.type=1 THEN 'ACTIVITY_RESUMED'
            when component_events.type=2 THEN 'ACTIVITY_PAUSED'
            else component_events.type
            END as eventType
            FROM component_events
            INNER JOIN components ON component_events.component_id=components._id
            INNER JOIN packages ON components.package_id=packages._id
            ORDER BY timestamp
            ''')

            all_rows = cursor.fetchall()
            usageentries = len(all_rows)
            if usageentries > 0:
                report = ArtifactHtmlReport('Wellbeing URL events')
                report.start_artifact_report(self.report_folder, 'URL Events')
                report.add_script()
                data_headers = ('Timestamp', 'Event ID', 'Package ID', 'Package Name', 'Website', 'Event')
                data_list = []
                for row in all_rows:
                    data_list.append((row[0], row[1], row[2], row[3], row[4], row[5]))

                report.write_artifact_data_table(data_headers, data_list, file_found)
                report.end_artifact_report()

                tsvname = f'wellbeing - URL events'
                tsv(self.report_folder, data_headers, data_list, tsvname)

                tlactivity = f'Wellbeing - URL Events'
                timeline(self.report_folder, tlactivity, data_list, data_headers)
            else:
                logfunc('No Wellbeing URL event data available')

            db.close()

        return True
