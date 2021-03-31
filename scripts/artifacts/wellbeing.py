from scripts.ilapfuncs import timeline, open_sqlite_db_readonly
from scripts.plugin_base import ArtefactPlugin
from scripts.artifact_report import ArtifactHtmlReport
from scripts.ilapfuncs import logfunc, tsv
from scripts import artifact_report

class WellbeingPlugin(ArtefactPlugin):
    """
    """

    def __init__(self):
        super().__init__()
        self.author = 'Unknown'
        self.author_email = ''
        self.author_url = ''

        self.name = 'Wellbeing - Events'
        self.description = ''

        self.artefact_reference = ''  # Description on what the artefact is.
        self.path_filters = ['**/com.google.android.apps.wellbeing/databases/app_usage*']  # Collection of regex search filters to locate an artefact.
        self.icon = ''  # feathricon for report.

        self.debug_mode = True

    def _processor(self) -> bool:

        for file_found in self.files_found:
            file_found = str(file_found)
            if not file_found.endswith('app_usage'):
                continue # Skip all other files

            db = open_sqlite_db_readonly(file_found)
            cursor = db.cursor()
            cursor.execute('''
            SELECT 
                    events._id, 
                    datetime(events.timestamp /1000, 'UNIXEPOCH') as timestamps, 
                    packages.package_name,
                    events.type,
                    case
                        when events.type = 1 THEN 'ACTIVITY_RESUMED'
                        when events.type = 2 THEN 'ACTIVITY_PAUSED'
                        when events.type = 12 THEN 'NOTIFICATION'
                        when events.type = 18 THEN 'KEYGUARD_HIDDEN & || Device Unlock'
                        when events.type = 19 THEN 'FOREGROUND_SERVICE_START'
                        when events.type = 20 THEN 'FOREGROUND_SERVICE_STOP' 
                        when events.type = 23 THEN 'ACTIVITY_STOPPED'
                        when events.type = 26 THEN 'DEVICE_SHUTDOWN'
                        when events.type = 27 THEN 'DEVICE_STARTUP'
                        else events.type
                        END as eventtype
                    FROM
                    events INNER JOIN packages ON events.package_id=packages._id 
            ''')

            all_rows = cursor.fetchall()
            usageentries = len(all_rows)
            if usageentries > 0:

                data_headers = ('Timestamp', 'Package ID', 'Event Type')
                data_list = []
                for row in all_rows:
                    data_list.append((row[1], row[2], row[4]))

                artifact_report.GenerateHtmlReport(self, file_found, data_headers, data_list)

                tsv(self.report_folder, data_headers, data_list, self.name)

                timeline(self.report_folder, self.name, data_list, data_headers)
            else:
                logfunc('No Wellbeing event data available')

            db.close()

        return True
