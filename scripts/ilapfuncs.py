import csv
import datetime
import os
import re
import sqlite3
import simplekml

from bs4 import BeautifulSoup


class OutputParameters:
    """Defines the parameters that are common for """
    # static parameters
    nl = '\n'
    screen_output_file_path = ''
    
    def __init__(self, output_folder):
        now = datetime.datetime.now()
        currenttime = now.strftime('%Y-%m-%d_%A_%H%M%S')
        self.report_folder_base = os.path.join(output_folder, 'ALEAPP_Reports_' + currenttime) # aleapp , aleappGUI, ileap_artifacts, report.py
        self.temp_folder = os.path.join(self.report_folder_base, 'temp')
        OutputParameters.screen_output_file_path = os.path.join(self.report_folder_base, 'Script Logs', 'Screen Output.html')

        os.makedirs(os.path.join(self.report_folder_base, 'Script Logs'), exist_ok = True)
        os.makedirs(self.temp_folder, exist_ok = True)


def is_platform_windows():
    """Returns True if running on Windows"""
    return os.name == 'nt'


def sanitize_file_path(filename, replacement_char='_'):
    """
    Removes illegal characters (for windows) from the string passed. Does not replace \ or /
    """
    return re.sub(r'[*?:"<>|\'\r\n]', replacement_char, filename)


def sanitize_file_name(filename, replacement_char='_'):
    """
    Removes illegal characters (for windows) from the string passed.
    """
    return re.sub(r'[\\/*?:"<>|\'\r\n]', replacement_char, filename)


def get_next_unused_name(path):
    """Checks if path exists, if it does, finds an unused name by appending -xx
       where xx=00-99. Return value is new path.
       If it is a file like abc.txt, then abc-01.txt will be the next
    """

    basename, ext = os.path.splitext(path)

    num = 2
    while os.path.exists(path):
        path = f'{basename}-{num:02}{ext}'
        num += 1

    return path


def open_sqlite_db_readonly(path):
    """Opens an sqlite db in read-only mode, so original db (and -wal/journal are intact)"""
    if is_platform_windows():

        url_encoded_prefix = '%5C%5C%3F%5C'  # URL escaped \\?\

        if (
            path.startswith('\\\\?\\UNC\\') or  # UNC long path
            path.startswith('\\\\?\\')  # normal long path
        ):
            path = url_encoded_prefix + path[4:]
        elif path.startswith('\\\\'):       # UNC path
            path = f'{url_encoded_prefix}\\UNC{path[1:]}'
        else:                               # normal path
            path = f'{url_encoded_prefix}{path}'
    return sqlite3.connect(f'file:{path}?mode=ro', uri=True)


def does_column_exist_in_db(db, table_name, col_name):
    """Checks if a specific col exists"""
    col_name = col_name.lower()
    query = f"pragma table_info('{table_name}');"
    all_rows = []

    try:
        db.row_factory = sqlite3.Row # For fetching columns by name
        cursor = db.cursor()
        cursor.execute(query)
        all_rows = cursor.fetchall()
    except sqlite3.Error as ex:
        print(f'Query error, query={query} Error={ex}')

    for row in all_rows:
        if row['name'].lower() == col_name:
            return True
    return False


def does_table_exist(db, table_name):
    """Checks if a table with specified name exists in an sqlite db"""
    query = f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'"
    row_count = 0

    try:
        cursor = db.execute(query)
        row_count = cursor.rowcount
    except sqlite3.Error as ex:
        logfunc(f'Query error, query={query} Error={ex}')

    if row_count >= 1:
        return True
    return False


class GuiWindow:
    """This only exists to hold window handle if script is run from GUI"""
    window_handle = None # static variable 
    progress_bar_total = 0
    progress_bar_handle = None

    @staticmethod
    def SetProgressBar(n):
        if GuiWindow.progress_bar_handle:
            GuiWindow.progress_bar_handle.UpdateBar(n)


def logfunc(message: str = ''):
    """
    Prints and writes a log message.
    Calls the GUI to be refreshed.
    :param message: Message to print.
    :return None:
    """
    print(message)
    with open(OutputParameters.screen_output_file_path, 'a', encoding='utf8') as a:
        a.write(message + OutputParameters.nl)

    if GuiWindow.window_handle:
        GuiWindow.window_handle.refresh()


# def deviceinfoin(ordes, kas, vas, sources): # unused function
#     sources = str(sources)
#     db = sqlite3.connect(reportfolderbase+'Device Info/di.db')
#     cursor = db.cursor()
#     datainsert = (ordes, kas, vas, sources,)
#     cursor.execute('INSERT INTO devinf (ord, ka, va, source)  VALUES(?,?,?,?)', datainsert)
#     db.commit()


def html2csv(reportfolderbase):
    """
    TODO: Consider removing, unused function.
    :param reportfolderbase: path to html files.
    :return:
    """

    # List of items that take too long to convert or that shouldn't be converted
    itemstoignore = ['index.html',
                    'Distribution Keys.html', 
                    'StrucMetadata.html',
                    'StrucMetadataCombined.html']

    path_csv_files = os.path.join(reportfolderbase, '_CSV Exports')

    os.makedirs(path_csv_files, exist_ok = True)

    for root, dirs, files in sorted(os.walk(reportfolderbase)):
        for file in files:
            if not file.endswith('.html') or file in itemstoignore:
                continue

            fullpath = (os.path.join(root, file))
            data = open(fullpath, 'r', encoding='utf8')
            soup = BeautifulSoup(data, 'html.parser')
            tables = soup.find_all('table')
            data.close()

            for table in tables:
                output_rows = []
                for table_row in table.findAll('tr'):

                    columns = table_row.findAll('td')
                    output_row = []
                    for column in columns:
                        output_row.append(column.text)
                    output_rows.append(output_row)

                file = os.path.splitext(file)[0]
                with open(os.path.join(path_csv_files,  file + '.csv'), mode='a', encoding='utf-8-sig') as csvfile:
                    writer = csv.writer(csvfile, quotechar='"', quoting=csv.QUOTE_ALL)
                    writer.writerows(output_rows)


def tsv(report_folder, data_headers, data_list, tsvname, source_file = None):
    # TODO: Add the paramter to record the file analysed.
    report_folder = report_folder.rstrip('/\\')
    report_folder_base, tail = os.path.split(report_folder)
    tsv_report_folder = os.path.join(report_folder_base, '_TSV Exports')

    os.makedirs(tsv_report_folder, exist_ok = True)

    tsv_file = os.path.join(tsv_report_folder, f'{tsvname}.tsv')
    tsv_file = get_next_unused_name(tsv_file)

    # Note: this shouldn't happen anyway due to the 'get unused name' call above.
    tsv_file_exists = os.path.exists(tsv_file)

    with open(tsv_file, mode='a', encoding='utf-8-sig') as tsvfile:
        tsv_writer = csv.writer(tsvfile, delimiter='\t')
        if not tsv_file_exists:

            if source_file is not None:
                # append source file to data header and list.
                data_headers = list(data_headers).append(source_file)
                for list_item in data_list:
                    list_item.append(source_file)

            tsv_writer.writerow(data_headers)

        tsv_writer.writerows(data_list)


def timeline(report_folder, tlactivity, data_list, data_headers):
    """
    Generates a timeline of events.

    :param report_folder:
    :param tlactivity:
    :param data_list:
    :param data_headers:
    :return:
    """

    report_folder = report_folder.rstrip('/\\')
    report_folder_base, tail = os.path.split(report_folder)
    tl_report_folder = os.path.join(report_folder_base, '_Timeline')

    os.makedirs(tl_report_folder, exist_ok = True)
    tldb = os.path.join(tl_report_folder, 'tl.db')

    try:
        if os.path.isfile(tldb):
            db = sqlite3.connect(tldb, isolation_level = 'exclusive')
            cursor = db.cursor()
            cursor.execute('''PRAGMA synchronous = EXTRA''')
            cursor.execute('''PRAGMA journal_mode = WAL''')
        else:
            db = sqlite3.connect(tldb, isolation_level = 'exclusive')
            cursor = db.cursor()
            cursor.execute(
                """
                    CREATE TABLE data(key TEXT, activity TEXT, datalist TEXT)
                """
            )
        db.commit()

        # TODO: format the data to correctly capitalise on the cursor.executemany method.
        # In the current state, this section of code is running a single insert query, many times, on a list containing a
        # single item. It is not taking advantage of the executemany capabilities where a large list can be provided.
        for data_item in data_list:
            modifiedList = list(map(lambda x, y: x + ': ' + str(y), data_headers, data_item))
            cursor.executemany("INSERT INTO data VALUES(?,?,?)", [(str(data_item[0]), tlactivity, str(modifiedList))])
        db.commit()
        db.close()
    except sqlite3.Error as ex:
        logfunc(f'Query error, Error={ex}')



def kmlgen(report_folder, kmlactivity, data_list, data_headers):
    report_folder = report_folder.rstrip('/\\')
    report_folder_base, tail = os.path.split(report_folder)
    kml_report_folder = os.path.join(report_folder_base, '_KML Exports')
    
    os.makedirs(kml_report_folder, exist_ok = True)
    latlongdb = os.path.join(kml_report_folder, '_latlong.db')
    kml = simplekml.Kml()

    try:
        if os.path.isfile(latlongdb):
            db = sqlite3.connect(latlongdb)
            cursor = db.cursor()
            cursor.execute('''PRAGMA synchronous = EXTRA''')
            cursor.execute('''PRAGMA journal_mode = WAL''')
        else:
            db = sqlite3.connect(latlongdb)
            cursor = db.cursor()
            cursor.execute(
                """
                    CREATE TABLE data(key TEXT, latitude TEXT, longitude TEXT, activity TEXT)
                """
            )
        db.commit()

        for data_item in data_list:
            modifiedDict = dict(zip(data_headers, data_item))
            times = modifiedDict.get('Timestamp', None)
            lon = modifiedDict.get('Longitude', 0)
            lat = modifiedDict.get('Latitude', 0)
            if (lat == 0 and lon == 0) and (times is not None):
                pnt = kml.newpoint()
                pnt.name = times
                pnt.description = f'Timestamp: {times} - {kmlactivity}'
                pnt.coords = [(lon, lat)]
                cursor.execute("INSERT INTO data VALUES(?,?,?,?)", (times, lat, lon, kmlactivity))

        db.commit()
        db.close()

    except sqlite3.Error as ex:
        logfunc(f'Query error, Error={ex}')

    kml.save(os.path.join(kml_report_folder, f'{kmlactivity}.kml'))


def convert_to_long_path(windows_path: str) -> str:
    """
    In Windows, path lengths have a limitation of 260 characters.
    This can be expanded to 32,767 characters by prepending the path with "\\?\"

    Reference: https://docs.microsoft.com/en-us/windows/win32/fileio/maximum-file-path-limitation

    :param windows_path:
    :return str: Long version of the file path suitable for Windows.
    """

    if is_platform_windows():
        return '\\\\?\\' + windows_path.replace('/', '\\')

    return windows_path
