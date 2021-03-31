import datetime

from scripts.ilapfuncs import timeline, open_sqlite_db_readonly
from scripts.plugin_base import ArtefactPlugin
from scripts.ilapfuncs import logfunc, tsv
from scripts import artifact_report


class WhatsAppMessagesPlugin(ArtefactPlugin):
    """
    """

    def __init__(self):
        super().__init__()
        self.author = 'Unknown'
        self.author_email = ''
        self.author_url = ''

        self.category = 'WhatsApp'
        self.name = 'Messages'
        self.description = ''

        self.artefact_reference = ''  # Description on what the artefact is.
        self.path_filters = ['*/com.whatsapp/databases/*.db*']  # Collection of regex search filters to locate an artefact.
        self.icon = 'message-square'  # feathricon for report.

    def _processor(self) -> bool:

        source_file_msg = ''
        whatsapp_msgstore_db = ''
        whatsapp_wa_db = ''

        for file_found in self.files_found:

            file_name = str(file_found)
            if file_name.endswith('msgstore.db'):
               whatsapp_msgstore_db = str(file_found)
               source_file_msg = file_found.replace(self.seeker.directory, '')

            if file_name.endswith('wa.db'):
               whatsapp_wa_db = str(file_found)

            db = open_sqlite_db_readonly(whatsapp_msgstore_db)
            cursor = db.cursor()

            cursor.execute('''attach database "''' + whatsapp_wa_db + '''" as wadb ''')

            try:
                cursor.execute('''
                            SELECT messages.key_remote_jid  AS id, 
                                   case 
                                      when contact_book_w_groups.recipients is null then messages.key_remote_jid
                                      else contact_book_w_groups.recipients
                                   end as recipients, 
                                   key_from_me              AS direction, 
                                   messages.data            AS content, 
                                   messages.timestamp/1000       AS send_timestamp, 
                                   messages.received_timestamp/1000, 
                                   case 
                                      when messages.remote_resource is null then messages.key_remote_jid 
                                      else messages.remote_resource
                                   end AS group_sender,
                                   messages.media_url       AS attachment
                            FROM   (SELECT jid, 
                                           recipients 
                                    FROM   wadb.wa_contacts AS contacts 
                                           left join (SELECT gjid, 
                                                             Group_concat(CASE 
                                                                            WHEN jid == "" THEN NULL 
                                                                            ELSE jid 
                                                                          END) AS recipients 
                                                      FROM   group_participants 
                                                      GROUP  BY gjid) AS groups 
                                                  ON contacts.jid = groups.gjid 
                                    GROUP  BY jid) AS contact_book_w_groups 
                                   join messages 
                                     ON messages.key_remote_jid = contact_book_w_groups.jid
                ''')

                all_rows = cursor.fetchall()
                usageentries = len(all_rows)
            except:
                usageentries = 0

            if usageentries > 0:

                data_headers = ('Send Timestamp', 'Received Timestamp', 'Message ID', 'Recipients', 'Direction', 'Content', 'Group Sender', 'Attachment')
                data_list = []
                for row in all_rows:
                    sendtime = datetime.datetime.fromtimestamp(int(row[4])).strftime('%Y-%m-%d %H:%M:%S')
                    receivetime = datetime.datetime.fromtimestamp(int(row[5])).strftime('%Y-%m-%d %H:%M:%S')

                    data_list.append((sendtime, receivetime, row[0], row[1], row[2], row[3], row[6], row[7]))

                artifact_report.GenerateHtmlReport(self, file_found, data_headers, data_list)

                tsv(self.report_folder, data_headers, data_list, self.full_name(), source_file_msg)

                timeline(self.report_folder, self.full_name(), data_list, data_headers)

            else:
                logfunc('No Whatsapp Message data available')

            db.close()

        return True
