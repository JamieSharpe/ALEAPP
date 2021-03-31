from scripts.ilapfuncs import timeline, kmlgen, open_sqlite_db_readonly
from scripts.plugin_base import ArtefactPlugin
from scripts.artifact_report import ArtifactHtmlReport
from scripts.ilapfuncs import logfunc, tsv
from scripts import artifact_report

class CmhPlugin(ArtefactPlugin):
    """
    """

    def __init__(self):
        super().__init__()
        self.author = 'Unknown'
        self.author_email = ''
        self.author_url = ''

        self.name = 'Samsung CMH'
        self.description = ''

        self.artefact_reference = ''  # Description on what the artefact is.
        self.path_filters = ['**/cmh.db']  # Collection of regex search filters to locate an artefact.
        self.icon = ''  # feathricon for report.

        self.debug_mode = True

    def _processor(self) -> bool:


        file_found = str(self.files_found[0])
        db = open_sqlite_db_readonly(file_found)
        cursor = db.cursor()
        cursor.execute('''
        SELECT
        datetime(images.datetaken /1000, "unixepoch") as datetaken,
        datetime(images.date_added, "unixepoch") as dateadded,
        datetime(images.date_modified, "unixepoch") as datemodified,
        images.title,
        images.bucket_display_name,
        images.latitude,
        images.longitude,
        location_view.address_text,
        location_view.uri,
        images._data,
        images.isprivate
        FROM images
        left join location_view
        on location_view._id = images._id
        ''')
        all_rows = cursor.fetchall()
        usageentries = len(all_rows)
        if usageentries > 0:
            data_headers = ('Timestamp', 'Date Added', 'Date Modified', 'Title', 'Bucket Name', 'Latitude', 'Longitude','Address', 'URI', 'Data Location', 'Is Private')
            data_list = []
            for row in all_rows:
                data_list.append((row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7], row[8], row[9], row[10]))

            artifact_report.GenerateHtmlReport(self, file_found, data_headers, data_list)

            tsvname = f'Samsung CMH Geodata'
            tsv(self.report_folder, data_headers, data_list, tsvname)

            tlactivity = f'Samsung CMH Geodata'
            timeline(self.report_folder, tlactivity, data_list, data_headers)

            kmlactivity = 'Samsung CMH Geodata'
            kmlgen(self.report_folder, kmlactivity, data_list, data_headers)

        else:
            logfunc(f'No Samsung_CMH_GeoData available')
        db.close()

        return True
