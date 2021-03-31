import datetime

from scripts.ilapfuncs import open_sqlite_db_readonly
from scripts.plugin_base import ArtefactPlugin
from scripts.ilapfuncs import logfunc, tsv
from scripts import artifact_report


class BrowserLocationPlugin(ArtefactPlugin):
    """
    """

    def __init__(self):
        super().__init__()
        self.author = 'Unknown'
        self.author_email = ''
        self.author_url = ''

        self.category = 'Geo Location'
        self.name = 'Browser'
        self.description = ''

        self.artefact_reference = ''  # Description on what the artefact is.
        self.path_filters = ['**/com.android.browser/app_geolocation/CachedGeoposition.db']  # Collection of regex search filters to locate an artefact.
        self.icon = 'map-pin'  # feathricon for report.

    def _processor(self) -> bool:

        source_file = ''

        for file_found in self.files_found:
            file_found = str(file_found)

            if file_found.endswith('-db'):
                source_file = file_found.replace(self.seeker.directory, '')
                continue

            source_file = file_found.replace(self.seeker.directory, '')

            db = open_sqlite_db_readonly(file_found)
            cursor = db.cursor()
            try:
                cursor.execute('''
                SELECT timestamp/1000, latitude, longitude, accuracy FROM CachedPosition;
                ''')

                all_rows = cursor.fetchall()
                usageentries = len(all_rows)
            except:
                usageentries = 0

            if usageentries > 0:
                data_headers = ('timestamp','latitude', 'longitude', 'accuracy') # Don't remove the comma, that is required to make this a tuple as there is only 1 element
                data_list = []
                for row in all_rows:
                    timestamp = datetime.datetime.fromtimestamp(int(row[0])).strftime('%Y-%m-%d %H:%M:%S')
                    data_list.append((timestamp, row[1], row[2], row[3]))

                artifact_report.GenerateHtmlReport(self, file_found, data_headers, data_list)

                tsv(self.report_folder, data_headers, data_list, self.full_name(), source_file)

            else:
                logfunc('No Browser Locations found')

            db.close()

        return True
