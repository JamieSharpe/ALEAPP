from scripts.ilapfuncs import timeline, open_sqlite_db_readonly
from scripts.plugin_base import ArtefactPlugin
from scripts.artifact_report import ArtifactHtmlReport
from scripts.ilapfuncs import logfunc, tsv


class AppInteractionPlugin(ArtefactPlugin):
    """
    """

    def __init__(self):
        super().__init__()
        self.author = 'Unknown'
        self.author_email = ''
        self.author_url = ''

        self.name = 'App Interaction'
        self.description = ''

        self.artefact_reference = ''  # Description on what the artefact is.
        self.path_filters = ['**/com.samsung.android.providers.context/databases/ContextLog.db']  # Collection of regex search filters to locate an artefact.
        self.icon = ''  # feathricon for report.

    def _processor(self) -> bool:

    
        file_found = str(self.files_found[0])
        db = open_sqlite_db_readonly(file_found)
        cursor = db.cursor()
        cursor.execute('''
        SELECT
        CASE WHEN starttime>0 THEN datetime(starttime /1000, 'UNIXEPOCH')
             ELSE ""
        END as date2,
        CASE WHEN stoptime>0 THEN datetime(stoptime /1000, 'UNIXEPOCH')
             ELSE ""
        END as date3,
        time_zone,
        app_id,
        app_sub_id,
        duration,
        duration/1000 as duraton_in_secs
        from use_app
        ''')

        all_rows = cursor.fetchall()
        usageentries = len(all_rows)
        if usageentries > 0:
            report = ArtifactHtmlReport('Samsung Context Log')
            report.start_artifact_report(self.report_folder, 'Samsung Context Log')
            report.add_script()
            data_headers = ('Start Time', 'Stop Time','Timezone', 'App ID', 'APP Sub ID', 'Duration', 'Duration in Secs')
            data_list = []
            for row in all_rows:
                data_list.append((row[0],row[1],row[2],row[3],row[4],row[5],row[6]))

            report.write_artifact_data_table(data_headers, data_list, file_found)
            report.end_artifact_report()

            tsvname = f'samsung contextlog'
            tsv(self.report_folder, data_headers, data_list, tsvname)

            tlactivity = f'Samsung Context Log'
            timeline(self.report_folder, tlactivity, data_list, data_headers)
        else:
            logfunc('No Samsung Context Log data available')

        db.close()
        return True
