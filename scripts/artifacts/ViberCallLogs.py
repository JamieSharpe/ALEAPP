from scripts.ilapfuncs import timeline, open_sqlite_db_readonly
from scripts.plugin_base import ArtefactPlugin
from scripts.artifact_report import ArtifactHtmlReport
from scripts.ilapfuncs import logfunc, tsv
from scripts import artifact_report

class ViberCallLogsPlugin(ArtefactPlugin):
    """
    """

    def __init__(self):
        super().__init__()
        self.author = 'Unknown'
        self.author_email = ''
        self.author_url = ''

        self.category = 'Viber'
        self.name = 'Call Logs'
        self.description = ''

        self.artefact_reference = ''  # Description on what the artefact is.
        self.path_filters = ['**/com.viber.voip/databases/*']  # Collection of regex search filters to locate an artefact.
        self.icon = ''  # feathricon for report.

    def _processor(self) -> bool:

        for file_found in self.files_found:

            if file_found.endswith('_data'):
                viber_data_db = str(file_found)

                db = open_sqlite_db_readonly(viber_data_db)
                cursor = db.cursor()
                try:
                    cursor.execute('''
                    SELECT
                    datetime(date/1000, 'unixepoch') AS start_time,
                    canonized_number,
                    case type
                        when 2 then "Outgoing"
                        else "Incoming"
                    end AS direction,
                    strftime('%H:%M:%S',duration, 'unixepoch') as duration,
                    case viber_call_type
                        when 1 then "Audio Call"
                        when 4 then "Video Call"
                        else "Unknown"
                    end AS viber_call_type
                    FROM calls
                    ''')

                    all_rows = cursor.fetchall()
                    usageentries = len(all_rows)
                except:
                    usageentries = 0

                if usageentries > 0:
                    data_headers = ('Call Start Time', 'Phone Number','Call Direction', 'Call Duration', 'Call Type') # Don't remove the comma, that is required to make this a tuple as there is only 1 element
                    data_list = []
                    for row in all_rows:
                        data_list.append((row[0], row[1], row[2], row[3], row[4]))

                    artifact_report.GenerateHtmlReport(self, file_found, data_headers, data_list)

                    tsv(self.report_folder, data_headers, data_list, self.full_name())

                    timeline(self.report_folder, self.name, data_list, data_headers)

                else:
                    logfunc('No Viber Call Logs found')

                db.close()

        return True
