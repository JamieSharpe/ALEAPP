from scripts.ilapfuncs import timeline, open_sqlite_db_readonly
from scripts.plugin_base import ArtefactPlugin
from scripts.artifact_report import ArtifactHtmlReport
from scripts.ilapfuncs import logfunc, tsv
from scripts import artifact_report


class CallLogPlugin(ArtefactPlugin):
    """
    """

    def __init__(self):
        super().__init__()
        self.author = 'Unknown'
        self.author_email = ''
        self.author_url = ''

        self.name = 'Call Logs'
        self.description = ''

        self.artefact_reference = ''  # Description on what the artefact is.
        self.path_filters = ['**/com.android.providers.contacts/databases/calllog.db']  # Collection of regex search filters to locate an artefact.
        self.icon = 'phone'  # feathricon for report.

    def _processor(self) -> bool:
    
        file_found = str(self.files_found[0])
        db = open_sqlite_db_readonly(file_found)
        cursor = db.cursor()
        cursor.execute('''
        SELECT
        datetime(date /1000, 'unixepoch') as date,
        CASE
            WHEN phone_account_address is NULL THEN ' '
            ELSE phone_account_address
            end as phone_account_address,
        number,
        CASE
            WHEN type = 1 THEN  'Incoming'
            WHEN type = 2 THEN  'Outgoing'
            WHEN type = 3 THEN  'Missed'
            WHEN type = 4 THEN  'Voicemail'
            WHEN type = 5 THEN  'Rejected'
            WHEN type = 6 THEN  'Blocked'
            WHEN type = 7 THEN  'Answered Externally'
            ELSE 'Unknown'
            end as types,
        duration,
        CASE
            WHEN geocoded_location is NULL THEN ' '
            ELSE geocoded_location
            end as geocoded_location,
        countryiso,
        CASE
            WHEN _data is NULL THEN ' '
            ELSE _data
            END as _data,
        CASE
            WHEN mime_type is NULL THEN ' '
            ELSE mime_type
            END as mime_type,
        CASE
            WHEN transcription is NULL THEN ' '
            ELSE transcription
            END as transcription,
        deleted
        FROM
        calls
        ''')

        all_rows = cursor.fetchall()
        usageentries = len(all_rows)
        if usageentries > 0:
            # report = ArtifactHtmlReport('Call logs')
            # report.start_artifact_report(self.report_folder, 'Call logs')
            # report.add_script()
            data_headers = ('Call Date', 'Phone Account Address', 'Partner', 'Type','Duration in Secs','Partner Location','Country ISO','Data','Mime Type','Transcription','Deleted')
            data_list = []
            for row in all_rows:
                # Setup icons for call type
                call_type = row[3]
                if   call_type == 'Incoming':  call_type_html = call_type + ' <i data-feather="phone-incoming" stroke="green"></i>'
                elif call_type == 'Outgoing':  call_type_html = call_type + ' <i data-feather="phone-outgoing" stroke="green"></i>'
                elif call_type == 'Missed':    call_type_html = call_type + ' <i data-feather="phone-missed" stroke="red"></i>'
                elif call_type == 'Voicemail': call_type_html = call_type + ' <i data-feather="voicemail" stroke="brown"></i>'
                elif call_type == 'Rejected':  call_type_html = call_type + ' <i data-feather="x" stroke="red"></i>'
                elif call_type == 'Blocked':   call_type_html = call_type + ' <i data-feather="phone-off" stroke="red"></i>'
                elif call_type == 'Answered Externally': call_type_html = call_type + ' <i data-feather="phone-forwarded"></i>'
                else:
                    call_type_html = call_type

                data_list.append((row[0], row[1], row[2], call_type_html, str(row[4]), row[5], row[6], row[7], row[8], row[9], str(row[10])))

            artifact_report.GenerateHtmlReport(self, file_found, data_headers, data_list, allow_html = True)
            # report.write_artifact_data_table(data_headers, data_list, file_found, html_escape=False)
            # report.end_artifact_report()

            tsvname = f'Call Logs'
            tsv(self.report_folder, data_headers, data_list, tsvname)

            tlactivity = 'Call Logs'
            timeline(self.report_folder, tlactivity, data_list, data_headers)
        else:
            logfunc('No Call Log data available')

        db.close()
        return True
