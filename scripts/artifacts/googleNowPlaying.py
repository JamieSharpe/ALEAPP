import blackboxprotobuf
import time

from html import escape
from scripts.ilapfuncs import timeline, is_platform_windows, open_sqlite_db_readonly
from scripts.plugin_base import ArtefactPlugin
from scripts.artifact_report import ArtifactHtmlReport
from scripts.ilapfuncs import logfunc, tsv
from scripts import artifact_report

is_windows = is_platform_windows()
slash = '\\' if is_windows else '/'


class GoogleNowPlayingPlugin(ArtefactPlugin):
    """
    """

    def __init__(self):
        super().__init__()
        self.author = 'Unknown'
        self.author_email = ''
        self.author_url = ''

        self.name = 'Google Now Playing'
        self.description = ''

        self.artefact_reference = 'This is data stored by the Now Playing feature in Pixel phones, which '\
                            'shows song data on the lock screen for any music playing nearby. It\'s ' \
                            'part of Pixel Ambient Services (https://play.google.com/store/apps/details?id=com.google.intelligence.sense).'  # Description on what the artefact is.
        self.path_filters = ['**/com.google.intelligence.sense/db/history_db*']  # Collection of regex search filters to locate an artefact.
        self.icon = ''  # feathricon for report.

        self.debug_mode = False

    def _processor(self) -> bool:
        for file_found in self.files_found:
            file_found = str(file_found)

            if file_found.find('{0}mirror{0}'.format(slash)) >= 0:
                # Skip sbin/.magisk/mirror/data/.. , it should be duplicate data
                continue
            elif not file_found.endswith('history_db'):
                continue # Skip all other files (-wal)

            db = open_sqlite_db_readonly(file_found)
            cursor = db.cursor()
            cursor.execute('''
            Select
            CASE
                timestamp 
                WHEN
                    "0" 
                THEN
                    "" 
                ELSE
                    datetime(timestamp / 1000, "unixepoch")
            END AS "timestamp",
            history_entry
            FROM
            recognition_history
            ''')
            all_rows = cursor.fetchall()
            usageentries = len(all_rows)
            if usageentries > 0:

                data_headers = ('Timestamp', 'Timezone', 'Song Title', 'Artist', 'Duration',
                                'Album', 'Album Year')
                data_list = []

                pb_types = {'9': {'type': 'message', 'message_typedef':
                            {
                            '6': {'type': 'double', 'name': ''} # This definition converts field to a double from generic fixed64
                            } }
                            }
                last_data_set = [] # Since there are a lot of similar entries differing only in timestamp, we can combine them.

                for row in all_rows:
                    timestamp = row[0]
                    pb = row[1]

                    data, actual_types = blackboxprotobuf.decode_message(pb, pb_types)
                    data = self.recursive_convert_bytes_to_str(data)

                    try:             timezones = self.FilterInvalidValue(data["7"])
                    except KeyError: timezones = ''

                    try:             songtitle = self.FilterInvalidValue(data["9"]["3"])
                    except KeyError: songtitle = ''

                    try:             artist = self.FilterInvalidValue(data["9"]["4"])
                    except KeyError: artist = ''

                    try:             durationinsecs = data["9"]["6"]
                    except KeyError: durationinsecs = ''

                    try:             album = self.FilterInvalidValue(data["9"]["13"])
                    except KeyError: album = ''

                    try:             year = self.FilterInvalidValue(data["9"]["14"])
                    except KeyError: year = ''

                    if durationinsecs:
                        duration = time.strftime('%H:%M:%S', time.gmtime(durationinsecs))
                    if not last_data_set:
                        last_data_set = [timestamp, escape(timezones), escape(songtitle), escape(artist), duration, escape(album), year]
                    elif self.AreContentsSame(last_data_set, timezones, songtitle, artist, duration, album, year):
                        if last_data_set[0] == timestamp: # exact duplicate, do not add
                            pass
                        else:
                            last_data_set[0] += ',\n' + timestamp
                    else:
                        data_list.append(last_data_set)
                        last_data_set = []
                if last_data_set:
                    data_list.append(last_data_set)
                logfunc("{} entries grouped into {}".format(usageentries, len(data_list)))
                artifact_report.GenerateHtmlReport(self, file_found, data_headers, data_list)

                tsvname = f'google now playing'
                tsv(self.report_folder, data_headers, data_list, tsvname)

                tlactivity = f'Google Now Playing'
                timeline(self.report_folder, tlactivity, data_list, data_headers)
            else:
                logfunc('No Now playing history')

            db.close()

        return True

    def recursive_convert_bytes_to_str(self, obj):
        '''Recursively convert bytes to strings if possible'''
        ret = obj
        if isinstance(obj, dict):
            for k, v in obj.items():
                obj[k] = self.recursive_convert_bytes_to_str(v)
        elif isinstance(obj, list):
            for index, v in enumerate(obj):
                obj[index] = self.recursive_convert_bytes_to_str(v)
        elif isinstance(obj, bytes):
            # test for string
            try:
                ret = obj.decode('utf8', 'backslashreplace')
            except UnicodeDecodeError:
                ret = str(obj)
        return ret

    def FilterInvalidValue(self, obj):
        '''Return obj if it is valid, else empty string'''
        # Remove any dictionary or list types
        if isinstance(obj, dict) or isinstance(obj, list):
            return ''
        return obj

    def AreContentsSame(self, last_data_set, timezones, songtitle, artist, duration, album, year):
        return last_data_set[1] == timezones and \
               last_data_set[2] == songtitle and \
               last_data_set[3] == artist and \
               last_data_set[4] == duration and \
               last_data_set[5] == album and \
               last_data_set[6] == year
