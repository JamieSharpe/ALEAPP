from scripts.ilapfuncs import timeline, open_sqlite_db_readonly
from scripts.plugin_base import ArtefactPlugin
from scripts.artifact_report import ArtifactHtmlReport
from scripts.ilapfuncs import logfunc, tsv
from scripts import artifact_report

class ViberMessagesPlugin(ArtefactPlugin):
    """
    """

    def __init__(self):
        super().__init__()
        self.author = 'Unknown'
        self.author_email = ''
        self.author_url = ''

        self.category = 'Viber'
        self.name = 'Messages'
        self.description = ''

        self.artefact_reference = ''  # Description on what the artefact is.
        self.path_filters = ['**/com.viber.voip/databases/*']  # Collection of regex search filters to locate an artefact.
        self.icon = ''  # feathricon for report.

        self.debug_mode = True

    def _processor(self) -> bool:

        for file_found in self.files_found:

            if file_found.endswith('_messages'):
                viber_messages_db = str(file_found)

                db = open_sqlite_db_readonly(viber_messages_db)
                cursor = db.cursor()
                try:
                    cursor.execute('''
                    SELECT 
                    datetime(M.msg_date/1000, 'unixepoch') AS msg_date,
                    convo_participants.from_number AS from_number, 
                    convo_participants.recipients AS recipients, 
                    M.conversation_id AS thread_id, 
                    M.body AS msg_content, 
                    case M.send_type
                        when 1 then "Outgoing" 
                        else "Incoming"
                    end AS direction, 
                    case M.unread 
                        when 0 then "Read" 
                        else "Unread" 
                    end AS read_status,
                    M.extra_uri AS file_attachment                            
                    FROM   (SELECT *, 
                                    group_concat(TO_RESULT.number) AS recipients 
                             FROM   (SELECT P._id     AS FROM_ID, 
                                            P.conversation_id, 
                                            PI.number AS FROM_NUMBER 
                                     FROM   participants AS P 
                                            JOIN participants_info AS PI 
                                              ON P.participant_info_id = PI._id) AS FROM_RESULT 
                                    JOIN (SELECT P._id AS TO_ID, 
                                                 P.conversation_id, 
                                                 PI.number 
                                          FROM   participants AS P 
                                                 JOIN participants_info AS PI 
                                                   ON P.participant_info_id = PI._id) AS TO_RESULT 
                                      ON FROM_RESULT.from_id != TO_RESULT.to_id 
                                         AND FROM_RESULT.conversation_id = TO_RESULT.conversation_id 
                             GROUP  BY FROM_RESULT.from_id) AS convo_participants 
                            JOIN messages AS M 
                              ON M.participant_id = convo_participants.from_id 
                                 AND M.conversation_id = convo_participants.conversation_id
                    ''')

                    all_rows = cursor.fetchall()
                    usageentries = len(all_rows)
                except:
                    usageentries = 0

                if usageentries > 0:
                    data_headers = ('Message Date', 'From Phone Number','Recipients', 'Thread ID', 'Message', 'Direction', 'Read Status', 'File Attachment') # Don't remove the comma, that is required to make this a tuple as there is only 1 element
                    data_list = []
                    for row in all_rows:
                        data_list.append((row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7]))

                    artifact_report.GenerateHtmlReport(self, file_found, data_headers, data_list)

                    tsv(self.report_folder, data_headers, data_list, self.name)

                    timeline(self.report_folder, self.name, data_list, data_headers)

                else:
                    logfunc('No Viber Messages found')

                db.close()

        return True
