import blackboxprotobuf

from scripts.ilapfuncs import timeline, is_platform_windows, open_sqlite_db_readonly
from scripts.plugin_base import ArtefactPlugin
from scripts.artifact_report import ArtifactHtmlReport
from scripts.ilapfuncs import logfunc, tsv
from scripts import artifact_report

is_windows = is_platform_windows()
slash = '\\' if is_windows else '/'


class UsageAppsPlugin(ArtefactPlugin):
    """
    """

    def __init__(self):
        super().__init__()
        self.author = 'Unknown'
        self.author_email = ''
        self.author_url = ''

        self.name = 'Personalisation Services'
        self.description = ''

        self.artefact_reference = 'This is data stored by the reflection_gel_events.db, which shows data usage from apps to included deleted apps.'  # Description on what the artefact is.
        self.path_filters = ['**/com.google.android.as/databases/reflection_gel_events.db*']  # Collection of regex search filters to locate an artefact.
        self.icon = ''  # feathricon for report.

        self.debug_mode = True

    def _processor(self) -> bool:

        for file_found in self.files_found:
            file_found = str(file_found)

            if file_found.find('{0}mirror{0}'.format(slash)) >= 0:
                # Skip sbin/.magisk/mirror/data/.. , it should be duplicate data
                continue
            elif not file_found.endswith('reflection_gel_events.db'):
                continue # Skip all other files (-wal, -journal)

            db = open_sqlite_db_readonly(file_found)
            cursor = db.cursor()
            cursor.execute('''
            SELECT
            datetime(timestamp /1000, 'UNIXEPOCH') as timestamp,
            id,
            proto,
            generated_from
            FROM
            reflection_event
            ''')
            all_rows = cursor.fetchall()
            usageentries = len(all_rows)

            if usageentries > 0:

                data_headers = ('Timestamp', 'Deleted?', 'BundleID', 'From', 'From in Proto', 'Proto Full')
                data_list = []
                types = (
                        {'1': {'type': 'bytes', 'name': ''},
                        '2': {'type': 'int', 'name': ''},
                        '5': {'type': 'message', 'message_typedef':
                        {'1': {'type': 'int', 'name': ''},
                        '6': {'type': 'fixed32', 'name': ''}}, 'name': ''},
                        '8': {'type': 'bytes', 'name': ''}}
                        )
                for row in all_rows:
                    timestamp = row[0]
                    idb = row[1]
                    pb = row[2]
                    generated = row[3]

                    if 'deleted_app' in idb:
                        pass
                    else:
                        idb = ''

                    values, actual_types = blackboxprotobuf.decode_message(pb, types)
                    values = self.recursive_convert_bytes_to_str(values)

                    for key, val in values.items():
                        #print(key, val)
                        if key == '1':
                            bundleid = val
                        if key == '5':
                            try:             timestamp = self.FilterInvalidValue(val['1'])
                            except KeyError: timestamp = ''

                            try:             usage = self.FilterInvalidValue(val['6'])
                            except KeyError: usage = ''
                        if key == '8':
                            source = val
                        else:
                            source =''

                    data_list.append((row[0], idb, bundleid, row[3], usage, values))
                artifact_report.GenerateHtmlReport(self, file_found, data_headers, data_list)

                tsv(self.report_folder, data_headers, data_list, self.name)

                timeline(self.report_folder, self.name, data_list, data_headers)
            else:
                logfunc('No Usage Apps data available')

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


