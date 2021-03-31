import datetime

from scripts.ilapfuncs import open_sqlite_db_readonly
from scripts.plugin_base import ArtefactPlugin
from scripts.ilapfuncs import logfunc, tsv
from scripts import artifact_report


class GoogleMapLocationPlugin(ArtefactPlugin):
    """
    """

    def __init__(self):
        super().__init__()
        self.author = 'Unknown'
        self.author_email = ''
        self.author_url = ''

        self.category = 'Geo Location'
        self.name = 'Google Map Location'
        self.description = ''

        self.artefact_reference = ''  # Description on what the artefact is.
        self.path_filters = ['**/com.google.android.location/files/cache.cell/cache.cell', '**/com.google.android.location/files/cache.wifi/cache.wifi']  # Collection of regex search filters to locate an artefact.
        self.icon = 'map-pin'  # feathricon for report.

    def _processor(self) -> bool:

        source_file = ''

        for file_found in self.files_found:
            file_found = str(file_found)

            if 'journal' in file_found:
                source_file = file_found.replace(self.seeker.directory, '')
                continue

            source_file = file_found.replace(self.seeker.directory, '')

            db = open_sqlite_db_readonly(file_found)
            cursor = db.cursor()
            try:
                cursor.execute('''
                SELECT time/1000, dest_lat, dest_lng, dest_title, dest_address, 
                       source_lat, source_lng FROM destination_history;
                ''')

                all_rows = cursor.fetchall()
                usageentries = len(all_rows)
            except:
                usageentries = 0

            if usageentries > 0:
                data_headers = ('timestamp','destination_latitude', 'destination_longitude', 'destination_title','destination_address', 'source_latitude', 'source_longitude')
                data_list = []
                for row in all_rows:
                    timestamp = datetime.datetime.fromtimestamp(int(row[0])).strftime('%Y-%m-%d %H:%M:%S')
                    data_list.append((timestamp, self.convertGeo(str(row[1])), self.convertGeo(str(row[2])), row[3], row[4], self.convertGeo(str(row[5])), self.convertGeo(str(row[6]))))

                artifact_report.GenerateHtmlReport(self, file_found, data_headers, data_list)

                tsv(self.report_folder, data_headers, data_list, self.full_name(), source_file)

            else:
                logfunc('No Google Map Locations found')

            db.close()

    def convertGeo(self, s):
        length = len(s)
        if length > 6:
            return (s[0: length - 6] + "." + s[length - 6: length])
        else:
            return (s)
