import glob
import json
import os
import shutil
import sqlite3
import xml.etree.ElementTree as ET

from scripts.ilapfuncs import is_platform_windows
from scripts.plugin_base import ArtefactPlugin
from scripts.artifact_report import ArtifactHtmlReport
from scripts.ilapfuncs import logfunc
from scripts import artifact_report


class RecentActivityPlugin(ArtefactPlugin):
    """
    """

    def __init__(self):
        super().__init__()
        self.author = 'Unknown'
        self.author_email = ''
        self.author_url = ''

        self.category = 'Recent Activity'
        self.name = 'Recent Tasks, Snapshots & Images'
        self.description = ''

        self.artefact_reference = ''  # Description on what the artefact is.
        self.path_filters = ['*/system_ce/*']  # Collection of regex search filters to locate an artefact.
        self.icon = 'activity'  # feathricon for report.

    def _processor(self) -> bool:

        slash = '\\' if is_platform_windows() else '/'

        self.custom_context = {
            'artefacts': []
        }
        # Filter for path xxx/yyy/system_ce/0
        for file_found in self.files_found:
            file_found = str(file_found)
            parts = file_found.split(slash)
            if len(parts) > 2 and parts[-2] == 'system_ce':
                uid = parts[-1]
                try:
                    uid_int = int(uid)
                    # Skip sbin/.magisk/mirror/data/system_ce/0 , it should be duplicate data??
                    if file_found.find('{0}mirror{0}'.format(slash)) >= 0:
                        continue
                    self.process_recentactivity(file_found, uid)
                except ValueError:
                    pass # uid was not a number

        if len(self.custom_context['artefacts']) > 0:
            artifact_report.GenerateHtmlReport(self, html_template = 'body_artefact_recent_activity.html', allow_html = True, custom_context = self.custom_context)

        return True

    def process_recentactivity(self, folder, uid):

        slash = '\\' if is_platform_windows() else '/'

        db = sqlite3.connect(os.path.join(self.report_folder, 'RecentAct_{}.db'.format(uid)))
        cursor = db.cursor()
        #Create table recent.
        cursor.execute('''
        CREATE TABLE 
        recent(task_id TEXT, effective_uid TEXT, affinity TEXT, real_activity TEXT, first_active_time TEXT, last_active_time TEXT,
        last_time_moved TEXT, calling_package TEXT, user_id TEXT, action TEXT, component TEXT, snap TEXT,recimg TXT, fullat1 TEXT, fullat2 TEXT)
        ''')
        db.commit()
        err = 0
        if self.report_folder[-1] == slash:
            folder_name = os.path.basename(self.report_folder[:-1])
        else:
            folder_name = os.path.basename(self.report_folder)

        for filename in glob.iglob(os.path.join(folder, 'recent_tasks', '**'), recursive=True):
            if os.path.isfile(filename): # filter dirs
                file_name = os.path.basename(filename)
                #logfunc(filename)
                #logfunc(file_name)
                #numid = file_name.split('_')[0]

                try:
                    ET.parse(filename)
                except ET.ParseError:
                    logfunc('Parse error - Non XML file? at: '+filename)
                    err = 1
                    #print(filename)

                if err == 1:
                    err = 0
                    continue
                else:
                    tree = ET.parse(filename)
                    root = tree.getroot()
                    #print('Processed: '+filename)
                    for child in root:
                        #All attributes. Get them in using json dump thing
                        fullat1 = json.dumps(root.attrib)
                        task_id = (root.attrib.get('task_id'))
                        effective_uid = (root.attrib.get('effective_uid'))
                        affinity = (root.attrib.get('affinity'))
                        real_activity = (root.attrib.get('real_activity'))
                        first_active_time = (root.attrib.get('first_active_time'))
                        last_active_time = (root.attrib.get('last_active_time'))
                        last_time_moved = (root.attrib.get('last_time_moved'))
                        calling_package = (root.attrib.get('calling_package'))
                        user_id = (root.attrib.get('user_id'))
                        #print(root.attrib.get('task_description_icon_filename'))

                        #All attributes. Get them in using json dump thing
                        fullat2 = json.dumps(child.attrib)
                        action = (child.attrib.get('action'))
                        component = (child.attrib.get('component'))
                        icon_image_path = (root.attrib.get('task_description_icon_filename'))

                        #Snapshot section picture
                        snapshot = task_id + '.jpg'
                        #print(snapshot)

                        #check for image in directories
                        check1 = os.path.join(folder, 'snapshots', snapshot)
                        isit1 = os.path.isfile(check1)
                        if isit1:
                            #copy snaphot image to report folder
                            shutil.copy2(check1, self.report_folder)
                            #snap = r'./snapshots/' + snapshot
                            snap = snapshot
                        else:
                            snap = 'NO IMAGE'
                        #Recent_images section
                        if icon_image_path is not None:
                            recent_image = os.path.basename(icon_image_path)
                            check2 = os.path.join(folder, 'recent_images', recent_image)
                            isit2 = os.path.isfile(check2)
                            if isit2:
                                shutil.copy2(check2, self.report_folder)
                                #recimg = r'./recent_images/' + recent_image
                                recimg = recent_image
                            else:
                                recimg = 'NO IMAGE'
                        else:
                            #check for other files not in the XML - all types
                            check3 = glob.glob(os.path.join(folder, 'recent_images', task_id, '*.*'))
                            if check3:
                                check3 = check3[0]
                                isit3 = os.path.isfile(check3)
                            else:
                                isit3 = 0

                            if isit3:
                                shutil.copy2(check3, self.report_folder)
                                recimg = os.path.basename(check3)
                            else:
                                recimg = 'NO IMAGE'
                        #else:
                        #    recimg = 'NO IMAGE'
                        #insert all items in database
                        cursor = db.cursor()
                        datainsert = (task_id, effective_uid, affinity, real_activity, first_active_time, last_active_time, last_time_moved, calling_package, user_id, action, component, snap, recimg, fullat1, fullat2,)
                        cursor.execute('INSERT INTO recent (task_id, effective_uid, affinity, real_activity, first_active_time, last_active_time, last_time_moved, calling_package, user_id, action, component, snap, recimg, fullat1, fullat2)  VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)', datainsert)
                        db.commit()

        # report = ArtifactHtmlReport('Recent Tasks, Snapshots & Images')
        location = os.path.join(folder, 'recent_tasks')
        # report.start_artifact_report(self.report_folder, f'Recent Activity_{uid}', f'Artifacts located at {location}')
        # report.add_script()



        #Query to create report
        db = sqlite3.connect(os.path.join(self.report_folder, 'RecentAct_{}.db'.format(uid)))
        cursor = db.cursor()

        #Query to create report
        cursor.execute('''
        SELECT 
            task_id as Task_ID, 
            effective_uid as Effective_UID, 
            affinity as Affinity, 
            real_activity as Real_Activity, 
            datetime(first_active_time/1000, 'UNIXEPOCH') as First_Active_Time, 
            datetime(last_active_time/1000, 'UNIXEPOCH') as Last_Active_Time,
            datetime(last_time_moved/1000, 'UNIXEPOCH') as Last_Time_Moved,
            calling_package as Calling_Package, 
            user_id as User_ID, 
            action as Action, 
            component as Component, 
            snap as Snapshot_Image, 
            recimg as Recent_Image
        FROM recent
        ''')
        all_rows = cursor.fetchall()
        colnames = cursor.description

        for row in all_rows:
            if row[2] is None:
                row2 = '' #'NO DATA'
            else:
                row2 = row[2]

            # report.write_minor_header(f'Application: {row2}')

            #do loop for headers
            data_list = []

            for x in range(0, 13):
                if row[x] is None:
                    pass
                else:
                    data_list.append((colnames[x][0], str(row[x])))


            data_headers = ('Key', 'Value')
            # report.write_artifact_data_table(data_headers, data_list, folder, table_id='', write_total=False, write_location=False, cols_repeated_at_bottom=False)

            image_data_row = []
            image_data_list = [image_data_row]

            if row[11] == 'NO IMAGE':
                image_data_row.append('No Image')
            else:
                image_data_row.append('<a href="{1}/{0}"><img src="{1}/{0}" class="img-fluid z-depth-2 zoom" style="max-height: 400px" title="{0}"></a>'.format(str(row[11]), folder_name))
            if row[12] == 'NO IMAGE':
                image_data_row.append('No Image')
            else:
                image_data_row.append('<a href="{1}/{0}"><img src="{1}/{0}" class="img-fluid z-depth-2 zoom" style="max-height: 400px" title="{0}"></a>'.format(str(row[12]), folder_name))

            image_data_headers = ('Snapshot_Image', 'Recent_Image')
            # report.write_artifact_data_table(image_data_headers, image_data_list, folder, table_id='', table_style="width: auto",
            #     write_total=False, write_location=False, html_escape=False, cols_repeated_at_bottom=False)

            self.custom_context['artefacts'].append(
            {
                'application_name': row2,
                'application_location': location,
                'application_keyvar_header': ('Key', 'Value'),
                'application_keyvar_data'  : data_list,
                'application_image_header': ('Snapshot_Image', 'Recent_Image'),
                'application_image_data': image_data_list
            })

            # report.write_raw_html('<br />')

        # report.end_artifact_report()
