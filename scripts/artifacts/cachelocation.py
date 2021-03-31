import datetime
import struct
import os

from scripts.ilapfuncs import timeline
from scripts.plugin_base import ArtefactPlugin
from scripts.ilapfuncs import logfunc, tsv
from scripts import artifact_report


class CacheLocationPlugin(ArtefactPlugin):
    """
    """

    def __init__(self):
        super().__init__()
        self.author = 'Unknown'
        self.author_email = ''
        self.author_url = ''

        self.category = 'Geo Location'
        self.name = 'Cache'
        self.description = ''

        self.artefact_reference = ''  # Description on what the artefact is.
        self.path_filters = ['**/com.google.android.location/files/cache.cell/cache.cell', '**/com.google.android.location/files/cache.wifi/cache.wifi']  # Collection of regex search filters to locate an artefact.
        self.icon = 'map-pin'  # feathricon for report.

    def _processor(self) -> bool:

        source_file = ''

        for file_found in self.files_found:

            file_name = str(file_found)
            source_file = file_found.replace(self.seeker.directory, '')

            data_list = []

            # code to parse the cache.wifi and cache.cell taken from https://forensics.spreitzenbarth.de/2011/10/28/decoding-cache-cell-and-cache-wifi-files/
            cacheFile = open(str(file_name), 'rb')
            (version, entries) = struct.unpack('>hh', cacheFile.read(4))
            # Check the number of entries * 32 (entry record size) to see if it is bigger then the file, this is a indication the file is malformed or corrupted
            cache_file_size = os.stat(file_name).st_size
            if ((entries * 32) < cache_file_size):
                i = 0
                while i < entries:
                    key = cacheFile.read(struct.unpack('>h', cacheFile.read(2))[0])
                    (accuracy, confidence, latitude, longitude, readtime) = struct.unpack('>iiddQ', cacheFile.read(32))
                    timestamp = readtime/1000
                    i = i + 1

                    starttime = datetime.datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
                    data_list.append((accuracy, confidence, latitude, longitude, starttime))
                cacheFile.close()

                data_headers = ('accuracy', 'confidence', 'latitude', 'longitude', 'readtime')

                artifact_report.GenerateHtmlReport(self, file_found, data_headers, data_list)

                tsv(self.report_folder, data_headers, data_list, self.full_name(), source_file)

                timeline(self.report_folder, self.full_name(), data_list, data_headers)

            else:
                logfunc('No Cachelocation Logs found')

