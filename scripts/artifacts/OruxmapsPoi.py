import datetime

from scripts.ilapfuncs import timeline, open_sqlite_db_readonly
from scripts.plugin_base import ArtefactPlugin
from scripts.ilapfuncs import logfunc, tsv
from scripts import artifact_report


class OruxMapsPoiPlugin(ArtefactPlugin):
    """
    """

    def __init__(self):
        super().__init__()
        self.author = 'Unknown'
        self.author_email = ''
        self.author_url = ''

        self.category = 'Oruxmaps'
        self.name = 'POI'
        self.description = 'Orux Maps Geo Location'

        self.artefact_reference = ''  # Description on what the artefact is.
        self.path_filters = ['*/oruxmaps/tracklogs/oruxmapstracks.db*']  # Collection of regex search filters to locate an artefact.
        self.icon = 'map'  # feathricon for report.

    def _processor(self) -> bool:
        file_found = str(self.files_found[0])
        # source_file = file_found.replace(seeker.directory, '')
        db = open_sqlite_db_readonly(file_found)
        cursor = db.cursor()

        cursor.execute('''
        SELECT poilat, poilon, poialt, poitime/1000, poiname FROM pois
        ''')

        all_rows = cursor.fetchall()
        usageentries = len(all_rows)
        if usageentries > 0:

            data_headers = ('poilat','poilon','poialt', 'poitime', 'poiname')
            data_list = []

            for row in all_rows:

                timestamp = datetime.datetime.fromtimestamp(int(row[3])).strftime('%Y-%m-%d %H:%M:%S')
                data_list.append((row[0], row[1], row[2], timestamp, row[4]))

            artifact_report.GenerateHtmlReport(self, file_found, data_headers, data_list)

            tsv(self.report_folder, data_headers, data_list, self.full_name())

            timeline(self.report_folder, self.full_name(), data_list, data_headers)
        else:
            logfunc('No Oruxmaps POI data available')

        db.close()

        return True
