from scripts.ilapfuncs import timeline, open_sqlite_db_readonly
from scripts.plugin_base import ArtefactPlugin
from scripts.artifact_report import ArtifactHtmlReport
from scripts.ilapfuncs import logfunc, tsv
from scripts import artifact_report

class SWellBeingPlugin(ArtefactPlugin):
    """
    """

    def __init__(self):
        super().__init__()
        self.author = 'Unknown'
        self.author_email = ''
        self.author_url = ''

        self.name = 'Samsung Wellbeing - Events'
        self.description = ''

        self.artefact_reference = ''  # Description on what the artefact is.
        self.path_filters = ['**/com.samsung.android.forest/databases/dwbCommon.db*']  # Collection of regex search filters to locate an artefact.
        self.icon = ''  # feathricon for report.

    def _processor(self) -> bool:

        for file_found in self.files_found:
            file_found = str(file_found)
            if not file_found.endswith('dwbCommon.db'):
                continue # Skip all other files

            db = open_sqlite_db_readonly(file_found)
            cursor = db.cursor()
            cursor.execute('''
            SELECT
            datetime(usageEvents.timeStamp/1000, "UNIXEPOCH") as timestamps,
            usageEvents.eventId,
            foundPackages.name, 
            usageEvents.eventType,
            CASE
            when usageEvents.eventType=1 THEN 'ACTIVITY_RESUMED'
            when usageEvents.eventType=2 THEN 'ACTIVITY_PAUSED'
            when usageEvents.eventType=5 THEN 'CONFIGURATION_CHANGE'
            when usageEvents.eventType=7 THEN 'USER_INTERACTION'
            when usageEvents.eventType=10 THEN 'NOTIFICATION PANEL'
            when usageEvents.eventType=11 THEN 'STANDBY_BUCKET_CHANGED'
            when usageEvents.eventType=12 THEN 'NOTIFICATION'
            when usageEvents.eventType=15 THEN 'SCREEN_INTERACTIVE (Screen on for full user interaction)'
            when usageEvents.eventType=16 THEN 'SCREEN_NON_INTERACTIVE (Screen on in Non-interactive state or completely turned off)'
            when usageEvents.eventType=17 THEN 'KEYGUARD_SHOWN || POSSIBLE DEVICE LOCK'
            when usageEvents.eventType=18 THEN 'KEYGUARD_HIDDEN || DEVICE UNLOCK'
            when usageEvents.eventType=19 THEN 'FOREGROUND_SERVICE START'
            when usageEvents.eventType=20 THEN 'FOREGROUND_SERVICE_STOP'
            when usageEvents.eventType=23 THEN 'ACTIVITY_STOPPED'
            when usageEvents.eventType=26 THEN 'DEVICE_SHUTDOWN'
            when usageEvents.eventType=27 THEN 'DEVICE_STARTUP'
            else usageEvents.eventType
            END as eventTypeDescription
            FROM usageEvents
            INNER JOIN foundPackages ON usageEvents.pkgId=foundPackages.pkgId
            
            ''')

            all_rows = cursor.fetchall()
            usageentries = len(all_rows)
            if usageentries > 0:
                data_headers = ('Timestamp','Event ID','Package Name','Event Type','Event Type Description')
                data_list = []
                for row in all_rows:
                    data_list.append((row[0], row[1], row[2], row[3], row[4]))

                artifact_report.GenerateHtmlReport(self, file_found, data_headers, data_list)

                tsv(self.report_folder, data_headers, data_list, self.full_name())

                timeline(self.report_folder, self.name, data_list, data_headers)
            else:
                logfunc('No Samsung Wellbeing event data available')

            db.close()

        return True
