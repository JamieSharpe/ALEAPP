import os
import shutil

from scripts.ilapfuncs import timeline, is_platform_windows, open_sqlite_db_readonly, get_next_unused_name
from scripts.plugin_base import ArtefactPlugin
from scripts.artifact_report import ArtifactHtmlReport
from scripts.ilapfuncs import logfunc, tsv
from scripts import artifact_report

is_windows = is_platform_windows()
slash = '\\' if is_windows else '/'


class CelloPlugin(ArtefactPlugin):
    """
    """

    def __init__(self):
        super().__init__()
        self.author = 'Unknown'
        self.author_email = ''
        self.author_url = ''

        self.category = 'Google Docs'
        self.name = 'Cello'
        self.description = ''

        self.artefact_reference = ''  # Description on what the artefact is.
        self.path_filters = [
            '*/com.google.android.apps.docs/app_cello/*/cello.db*',
            '*/com.google.android.apps.docs/files/shiny_blobs/blobs/*'
        ]  # Collection of regex search filters to locate an artefact.
        self.icon = 'file'  # feathricon for report.

        self.debug_mode = True

    def _processor(self) -> bool:
        file_found = self.get_cello_db_path(self.files_found)
        if not file_found:
            logfunc('Error: Could not get Cello.db path')
            return

        if self.report_folder[-1] == slash:
            folder_name = os.path.basename(self.report_folder[:-1])
        else:
            folder_name = os.path.basename(self.report_folder)

        db = open_sqlite_db_readonly(file_found)
        cursor = db.cursor()
        cursor.execute('''
        SELECT
            case created_date
                when 0 then ''
                else datetime(created_date/1000, 'unixepoch')
            end as created_date,
            title,
            case modified_date
                when 0 then ''
                else datetime(modified_date/1000, 'unixepoch')
            end as modified_date,
            case shared_with_me_date
                when 0 then ''
                else datetime(shared_with_me_date/1000, 'unixepoch')
            end as shared_with_me_date,
            case modified_by_me_date
                when 0 then ''
                else datetime(modified_by_me_date/1000, 'unixepoch')
            end as modified_by_me_date,
            case viewed_by_me_date
                when 0 then ''
                else datetime(viewed_by_me_date/1000, 'unixepoch')
            end as viewed_by_me_date,
            mime_type,
            Quota_bytes,
            case is_folder
                when 0 then ''
                when 1 then 'Yes'
            end as is_folder,
            case is_owner
                when 0 then ''
                when 1 then 'Yes'
            end as is_owner,
            case trashed
                when 0 then ''
                when 1 then 'Yes'
            end as trashed,
            (SELECT value from item_properties where key='offlineStatus' and item_stable_id=stable_id) as offline_status,
            (SELECT json_extract(value, '$.blobKey') from item_properties where key LIKE 'com.google.android.apps.docs:content_metadata%' and item_stable_id=stable_id) as content_metadata
        FROM items
        ''')

        all_rows = cursor.fetchall()
        usageentries = len(all_rows)
        if usageentries > 0:
            data_headers = ('Created Date','File Name','Modified Date','Shared with User Date','Modified by User Date','Viewed by User Date','Mime Type', \
                            'Offline','Quota Size','Folder','User is Owner','Deleted')
            data_list = []
            tsv_list = []
            for row in all_rows:
                doc_name = row[1]
                offline_status = "No"
                if row[11] == 1: # file is offline
                    offline_status = "Yes"
                    offline_path_name = row[12]
                    if offline_path_name not in (None, ''):
                        offline_path = self.get_offline_path(self.files_found, offline_path_name)
                        if offline_path:
                            destination_path = get_next_unused_name(os.path.join(self.report_folder, doc_name))
                            shutil.copy2(offline_path, destination_path)
                            dest_name = os.path.basename(destination_path)
                            doc_name = f"<a href=\"{folder_name}/{dest_name}\" target=\"_blank\" style=\"color:green; font-weight:bolder\">{doc_name}</a>"
                        else:
                            logfunc(f'File {doc_name} not present offline!')
                    else:
                        logfunc(f'File {doc_name} not present offline!')
                if row[8] == "Yes":
                    doc_name = '<i data-feather="folder"></i> ' + doc_name
                else:
                    if doc_name.startswith('<a href'):
                        doc_name = '<i data-feather="file" stroke="green"></i> ' + doc_name
                    else:
                        doc_name = '<i data-feather="file"></i> ' + doc_name
                data_list.append((row[0],doc_name,row[2],row[3],row[4],row[5],row[6],offline_status,row[7],row[8],row[9],row[10]))
                tsv_list.append((row[0],row[1],row[2],row[3],row[4],row[5],row[6],offline_status,row[7],row[8],row[9],row[10]))

            artifact_report.GenerateHtmlReport(self, file_found, data_headers, data_list, allow_html = True)

            tsvname = f'Google Drive - Cello'
            tsv(self.report_folder, data_headers, tsv_list, tsvname)

            tlactivity = f'Google Drive - Cello'
            timeline(self.report_folder, tlactivity, tsv_list, data_headers)
        else:
            logfunc('No Google Drive - Cello data available')

        db.close()
        return True

    def get_cello_db_path(self, files_found):
        for file_found in files_found:
            file_found = str(file_found)
            if not os.path.basename(file_found) == 'cello.db': # skip -journal and other files
                continue
            elif file_found.find('.magisk') >= 0 and file_found.find('mirror') >= 0:
                continue # Skip sbin/.magisk/mirror/data/.. , it should be duplicate data??
            return file_found
        return ''

    def get_offline_path(self, files_found, blob_name):
        # offline_path_relative = "/files/shiny_blobs/blobs"
        for file_found in files_found:
            if file_found.endswith(blob_name):
                file_found = str(file_found)
                return file_found
        return ''
