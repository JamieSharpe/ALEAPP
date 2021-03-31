from scripts.ilapfuncs import timeline, open_sqlite_db_readonly
from scripts.plugin_base import ArtefactPlugin
from scripts.artifact_report import ArtifactHtmlReport
from scripts.ilapfuncs import logfunc, tsv


class SMembersPlugin(ArtefactPlugin):
    """
    """

    def __init__(self):
        super().__init__()
        self.author = 'Unknown'
        self.author_email = ''
        self.author_url = ''

        self.name = 'App Interactive'
        self.description = ''

        self.artefact_reference = ''  # Description on what the artefact is.
        self.path_filters = ['**/com.samsung.oh/databases/com_pocketgeek_sdk_app_inventory.db']  # Collection of regex search filters to locate an artefact.
        self.icon = ''  # feathricon for report.

    def _processor(self) -> bool:

        file_found = str(self.files_found[0])
        db = open_sqlite_db_readonly(file_found)
        cursor = db.cursor()
        cursor.execute('''
        select
        datetime(last_used / 1000, "unixepoch"),  
        display_name, 
        package_name, 
        system_app, 
        confidence_hash,
        sha1,
        classification
        from android_app
        ''')

        all_rows = cursor.fetchall()
        usageentries = len(all_rows)
        if usageentries > 0:
            report = ArtifactHtmlReport('Samsung Members - Apps')
            report.start_artifact_report(self.report_folder, 'Samsung Members - Apps')
            report.add_script()
            data_headers = ('Timestamp','Display Name','Package Name','System App?','Confidence Hash','SHA1','Classification' )
            data_list = []
            for row in all_rows:
                data_list.append((row[0],row[1],row[2],row[3],row[4],row[5],row[6]))

            report.write_artifact_data_table(data_headers, data_list, file_found)
            report.end_artifact_report()

            tsvname = f'samsung members - apps'
            tsv(self.report_folder, data_headers, data_list, tsvname)

            tlactivity = f'Samsung Members - Apps'
            timeline(self.report_folder, tlactivity, data_list, data_headers)
        else:
            logfunc('No Samsung Members - Apps data available')

        db.close()

        return True
