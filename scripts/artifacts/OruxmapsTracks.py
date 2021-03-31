import datetime

from scripts.ilapfuncs import timeline, open_sqlite_db_readonly
from scripts.plugin_base import ArtefactPlugin
from scripts.ilapfuncs import logfunc, tsv
from scripts import artifact_report


class OruxMapsTracksPlugin(ArtefactPlugin):
    """
    """

    def __init__(self):
        super().__init__()
        self.author = 'Unknown'
        self.author_email = ''
        self.author_url = ''

        self.category = 'Oruxmaps'
        self.name = 'Tracks'
        self.description = 'Orux Maps Tracks'

        self.artefact_reference = ''  # Description on what the artefact is.
        self.path_filters = ['**/oruxmaps/tracklogs/oruxmapstracks.db*']  # Collection of regex search filters to locate an artefact.
        self.icon = 'map-pin'  # feathricon for report.

    def _processor(self) -> bool:
        file_found = str(self.files_found[0])
        # source_file = file_found.replace(seeker.directory, '')
        db = open_sqlite_db_readonly(file_found)
        cursor = db.cursor()

        cursor.execute('''
                SELECT tracks._id, trackname, trackciudad, segname, trkptlat, trkptlon, trkptalt, trkpttime/1000 
                  FROM tracks, segments, trackpoints
                 where tracks._id = segments.segtrack and segments._id = trackpoints.trkptseg
        ''')

        all_rows = cursor.fetchall()
        usageentries = len(all_rows)
        if usageentries > 0:
            data_headers = ('track id','track name','track description', 'segment name', 'latitude', 'longitude', 'altimeter', 'datetime') # Don't remove the comma, that is required to make this a tuple as there is only 1 element
            data_list = []

            for row in all_rows:
                timestamp = datetime.datetime.fromtimestamp(int(row[7])).strftime('%Y-%m-%d %H:%M:%S')
                data_list.append((row[0], row[1], row[2], row[3], row[4], row[5], row[6], timestamp))

            artifact_report.GenerateHtmlReport(self, file_found, data_headers, data_list)

            tsv(self.report_folder, data_headers, data_list, self.full_name())

            timeline(self.report_folder, self.full_name(), data_list, data_headers)
        else:
            logfunc('No Oruxmaps Tracks data available')

        db.close()

        return True
