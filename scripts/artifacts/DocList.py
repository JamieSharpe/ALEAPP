from scripts.ilapfuncs import timeline, open_sqlite_db_readonly
from scripts.plugin_base import ArtefactPlugin
from scripts.artifact_report import ArtifactHtmlReport
from scripts.ilapfuncs import logfunc, tsv
from scripts import artifact_report

class Plugin(ArtefactPlugin):
    """
    """

    def __init__(self):
        super().__init__()
        self.author = 'Unknown'
        self.author_email = ''
        self.author_url = ''

        self.name = 'Google Drive - Doc List'
        self.description = ''

        self.artefact_reference = ''  # Description on what the artefact is.
        self.path_filters = ['*/com.google.android.apps.docs/databases/DocList.db*']  # Collection of regex search filters to locate an artefact.
        self.icon = 'file'  # feathricon for report.

    def _processor(self) -> bool:
    
        file_found = str(self.files_found[0])
        db = open_sqlite_db_readonly(file_found)
        cursor = db.cursor()
        try:
            cursor.execute('''
            select
                case creationTime
                    when 0 then ''
                    else datetime("creationTime"/1000, 'unixepoch')
                end as creationTime,
                title,
                owner,
                case lastModifiedTime
                    when 0 then ''
                    else datetime("lastModifiedTime"/1000, 'unixepoch') 
                end as lastModifiedTime,
                case lastOpenedTime
                    when 0 then ''
                    else datetime("lastOpenedTime"/1000, 'unixepoch')
                end as lastOpenedTime,
                lastModifierAccountAlias,
                lastModifierAccountName,
                kind,
                shareableUri,
                htmlUri,
                md5Checksum,
                size
            from EntryView
            ''')

            all_rows = cursor.fetchall()
            usageentries = len(all_rows)
        except:
            usageentries = 0

        if usageentries > 0:
            data_headers = ('Created Date','File Name','Owner','Modified Date','Opened Date','Last Modifier Account Alias','Last Modifier Account Name','File Type','Shareable URI','HTML URI','MD5 Checkusm','Size') # Don't remove the comma, that is required to make this a tuple as there is only 1 element
            data_list = []
            for row in all_rows:
                data_list.append((row[0],row[1],row[2],row[3],row[4],row[5],row[6],row[7],row[8],row[9],row[10],row[11],))

            artifact_report.GenerateHtmlReport(self, file_found, data_headers, data_list)

            tsv(self.report_folder, data_headers, data_list, self.full_name())

            timeline(self.report_folder, self.name, data_list, data_headers)
        else:
            logfunc('No Google Drive - DocList data available')

        db.close()

        return True
