from scripts.ilapfuncs import timeline, open_sqlite_db_readonly
from scripts.plugin_base import ArtefactPlugin
from scripts.artifact_report import ArtifactHtmlReport
from scripts.ilapfuncs import logfunc, tsv
from scripts import artifact_report

class WellbeingUrlsPlugin(ArtefactPlugin):
    """
    """

    def __init__(self):
        super().__init__()
        self.author = 'Unknown'
        self.author_email = ''
        self.author_url = ''

        self.category = 'Wellbeing'
        self.name = 'URL Events'
        self.description = ''

        self.artefact_reference = ''  # Description on what the artefact is.
        self.path_filters = ['**/com.google.android.apps.wellbeing/databases/app_usage*']  # Collection of regex search filters to locate an artefact.
        self.icon = 'list'  # feathricon for report.

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
                data_headers = ('Timestamp', 'Event ID', 'Package ID', 'Package Name', 'Website', 'Event')
                data_list = []
                for row in all_rows:
                    data_list.append((row[0], row[1], row[2], row[3], row[4], row[5]))

                artifact_report.GenerateHtmlReport(self, file_found, data_headers, data_list)

                tsv(self.report_folder, data_headers, data_list, self.full_name())

                timeline(self.report_folder, self.name, data_list, data_headers)
            else:
                logfunc('No Wellbeing URL event data available')

            db.close()

        return True
