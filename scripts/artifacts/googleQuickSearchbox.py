import blackboxprotobuf
import datetime
import os
import struct
from html import escape

from scripts.ilapfuncs import timeline, is_platform_windows
from scripts.plugin_base import ArtefactPlugin
from scripts.artifact_report import ArtifactHtmlReport
from scripts.ilapfuncs import logfunc, tsv
from scripts import artifact_report

is_windows = is_platform_windows()
slash = '\\' if is_windows else '/'


class Session:
    # Represents a search query session
    def __init__(self, source_file, file_last_mod_date, session_type, session_from, session_queries, mp3_path):
        self.source_file = source_file
        self.file_last_mod_date = file_last_mod_date
        self.session_type = session_type
        self.session_from = session_from
        self.session_queries = session_queries
        self.mp3_path = mp3_path


class GoogleQuickSearchPlugin(ArtefactPlugin):
    """
    """

    def __init__(self):
        super().__init__()
        self.author = 'Unknown'
        self.author_email = ''
        self.author_url = ''

        self.category = 'Google Now & QuickSearch'
        self.name = 'Google App & Quick Search Queries'
        self.description = 'Recently searched terms from the Google Search widget and any interaction with the Google Personal Assistant / app (previously known as \'Google Now\') appear here. This can include previously searched items from another device too!'

        self.artefact_reference = 'Recently searched terms from the Google Search widget and any interaction with the Google Personal Assistant / app (previously known as \'Google Now\') appear here. This can include previously searched items from another device too!'
        self.path_filters = ['*/com.google.android.googlequicksearchbox/app_session/*.binarypb']  # Collection of regex search filters to locate an artefact.
        self.icon = 'search'  # feathricon for report.

    def _processor(self) -> bool:

        sessions = []
        base_folder = ''
        for file_found in self.files_found:

            if file_found.find('{0}mirror{0}'.format(slash)) >= 0:
                # Skip sbin/.magisk/mirror/data/.. , it should be duplicate data
                continue
            elif os.path.isdir(file_found): # skip folders (there shouldn't be any)
                continue

            base_folder = os.path.dirname(file_found)
            file_name = os.path.basename(file_found)
            with open(file_found, 'rb') as f:
                pb = f.read()
                values, types = blackboxprotobuf.decode_message(pb)
                file_last_mod_date = str(self.ReadUnixTime(os.path.getmtime(file_found)))
                s = self.parse_session_data(values, file_name, file_last_mod_date, self.report_folder)
                sessions.append(s)

        if self.report_folder[-1] == slash:
            folder_name = os.path.basename(self.report_folder[:-1])
        else:
            folder_name = os.path.basename(self.report_folder)
        entries = len(sessions)
        if entries > 0:
            data_headers = ('File Timestamp', 'Type', 'Queries', 'Response', 'Source File')
            data_list = []
            for s in sessions:
                response = ''
                if s.mp3_path:
                    filename = os.path.basename(s.mp3_path)
                    response = f'<audio controls><source src="{folder_name}/{filename}"></audio>'
                data_list.append( (s.file_last_mod_date, s.session_type, escape(', '.join(s.session_queries)), response, s.source_file) )

            artifact_report.GenerateHtmlReport(self, file_found, data_headers, data_list, allow_html = True)

            tsv(self.report_folder, data_headers, data_list, self.full_name())

            timeline(self.report_folder, self.name, data_list, data_headers)
        else:
            logfunc('No recent quick search or now data available')

        return True

    def ReadUnixTime(self, unix_time):  # Unix timestamp is time epoch beginning 1970/1/1
        '''Returns datetime object, or empty string upon error'''
        if unix_time not in (0, None, ''):
            try:
                if isinstance(unix_time, str):
                    unix_time = float(unix_time)
                return datetime.datetime(1970, 1, 1) + datetime.timedelta(seconds = unix_time)
            except (ValueError, OverflowError, TypeError) as ex:
                logfunc(
                    "ReadUnixTime() Failed to convert timestamp from value " + str(unix_time) + " Error was: " + str(
                        ex))
        return ''

    def get_search_query_from_blob(self, data):
        term = 'com.google.android.apps.gsa.shared.search.Query'.encode('utf-16')[2:]
        query = ''
        pos = data.find(term + b'\0\0')
        if pos > 0:
            if pos % 4:
                pos += 2
            pos += 96  # skip term
            # if data[pos : pos + 2] in (b'\x01\x4C', b'\x01\x0C'):
            if data[pos: pos + 2] != b'\x03\x00':
                pos += 20
                str_len = struct.unpack('<I', data[pos:pos + 4])[0]
                if str_len > 0:
                    pos += 4
                    query = data[
                            pos: pos + str_len * 2]  # TODO PROBLEM - With Android 11, this is utf8! No indication of format anywhere
                    if data[pos + str_len: pos + str_len + 1] == b'\0':  # then its utf8
                        query = query[:str_len].decode('utf8', 'ignore')
                    else:
                        query = query.decode('utf-16', 'backslashreplace')
        return query

    def parse_session_data(self, values, file_name, file_last_mod_date, report_folder):
        '''Parse protobuf dictionary and return a session object'''
        empty_dict = dict()
        session_type = values.get('3', b'').decode('utf8')
        session_from = values.get('146514374', empty_dict).get('1', b'').decode('utf8')
        session_queries = []
        main_query = ''
        mp3_path = ''

        # Main/Last query is in values['132269847']['1']['2']
        try:
            item = values['132269847']['1']['2']
            if item and isinstance(item, bytes):
                item = item.decode('utf8', 'backslashreplace')
                if item:
                    main_query = item
        except (KeyError, ValueError, TypeError):
            pass

        # Get other queries
        try:
            items = values['132269847']['2']
            if isinstance(items, list):
                for item in items:
                    if isinstance(item, bytes):
                        term = self.get_search_query_from_blob(item)
                        if term:
                            session_queries.append(term)

        except (KeyError, ValueError, TypeError):
            pass

        # main_query is typically the last query or only query. If not in session_queries, add it
        if session_queries and main_query:
            try:
                idx = session_queries.index(main_query)
            except ValueError:  # not found
                # add to session_queries
                session_queries.append(main_query)

        session_queries = [f'"{x}"' for x in session_queries]

        # Get mp3 recording of response
        try:
            data = values['132269388']['1']
            if isinstance(data, bytes):
                mp3_path = os.path.join(report_folder, os.path.splitext(file_name)[0] + ".mp3")
                f = open(mp3_path, 'wb')
                f.write(data)
                f.close()
        except (KeyError, ValueError):
            pass

        return Session(file_name, file_last_mod_date, session_type, session_from, session_queries, mp3_path)
