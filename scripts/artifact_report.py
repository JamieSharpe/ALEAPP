import html
import os
import sys
import uuid
import shutil
from distutils.dir_util import copy_tree
from datetime import datetime

from scripts.ilapfuncs import get_next_unused_name
from jinja2 import Environment, select_autoescape, FileSystemLoader
from scripts.html_parts import *
from scripts.ilapfuncs import is_platform_windows
from scripts.version_info import aleapp_version, aleapp_contributors

GeneratedHtmlReports = {}


def CopyStaticFiles(report_folder):
    static_resources = resource_path('scripts\\html_templates')
    copy_tree(os.path.join(static_resources, 'static'), os.path.join(report_folder, 'static'))
    for root, dirs, files in sorted(os.walk(report_folder)):
        for dir in dirs:
            # Delete temp html reports
            if dir == 'HTML Reports - Temp':
                shutil.rmtree(os.path.join(root, dir))

            # Delete empty folders
            if len(os.listdir(root)) == 0:
                shutil.rmtree(root)


def compilenavbar():
    resource_base_html = resource_path('scripts\\html_templates', 'base.html')
    template_loader = FileSystemLoader(searchpath = os.path.dirname(resource_base_html))
    # autoescape HTML characters for security.
    env = Environment(
            loader = template_loader,
            autoescape = select_autoescape(['html', 'xml'])
    )

    context = {
        'navbar': GeneratedHtmlReports,
    }

    template = env.get_template('navbar.html')
    html_content = template.render(context = context)
    return html_content


def CompileIndex(report_folder, input_path, extraction_type, processing_time):
    # compile the index page using the compiled navbar
    resource_base_html = resource_path('scripts\\html_templates', 'base.html')
    template_loader = FileSystemLoader(searchpath = os.path.dirname(resource_base_html))

    # Get script run log (this will be tab2)
    script_log_path = os.path.join(report_folder, 'Script Logs', 'Screen Output.html')
    with open(script_log_path, mode = 'r', encoding = 'utf-8') as f:
        script_log_content = f.readlines()

    # Get processed files list (this will be tab3)
    processed_files_path = os.path.join(report_folder, 'Script Logs', 'ProcessedFilesLog.html')
    with open(processed_files_path, mode = 'r', encoding = 'utf-8') as f:
        process_log_content = f.readlines()

    # autoescape HTML characters for security.
    env = Environment(
            loader = template_loader,
            autoescape = select_autoescape(['html', 'xml'])
    )
    context = {
        'version': aleapp_version,
        'title': 'Home',
        'navbar': compilenavbar(),
        'case_information': {
            'rows':
                [
                    ['Extraction Location', input_path],
                    ['Extraction Type', extraction_type],
                    ['Date of Report', datetime.now().strftime('%Y-%m-%d - %H:%M:%S')],
                    ['Report Directory', report_folder],
                    ['Processing Time', processing_time]
                ]
        },
        'run_log': {
            'file_title': 'Run Log',
            'file_lines': script_log_content
        },
        'file_log': {
            'file_title': 'File Process Log',
            'file_lines': process_log_content
        },
        'contributors': aleapp_contributors,
    }
    template = env.get_template('body_index.html')
    html_content = template.render(context = context)

    path_index = os.path.join(report_folder, 'index.html')
    with open(path_index, mode = 'w', encoding = 'utf-8') as f:
        f.write(html_content)


def CompileAllHTMLReports(report_folder):
    """
    Gets all the .temphtml files and compiles them with the correct navigation bar.

    :return:
    """
    for root, dirs, files in sorted(os.walk(report_folder)):
        for file in files:
            if file.endswith(".temphtml"):
                print(file)

                with open(os.path.join(root, file), mode = 'r', encoding = 'utf-8') as file_report:
                    file_content = file_report.read()

                resource_base_html = resource_path('scripts\\html_templates', 'base.html')
                template_loader = FileSystemLoader(searchpath = os.path.dirname(resource_base_html))
                # autoescape HTML characters for security.
                env = Environment(
                        loader = template_loader,
                        autoescape = select_autoescape(['html', 'xml'])
                )

                file, ext = os.path.splitext(file)
                artefact_name = file[file.index('_') + 1:]

                context = {
                    'version': aleapp_version,
                    'title': f'{artefact_name} report',
                    'navbar': compilenavbar(),
                    'main_body': file_content,
                }

                template = env.get_template('base.html')
                html_content = template.render(context = context)
                with open(os.path.join(report_folder, f'{file}.html'), mode = 'w', encoding = 'utf-8') as f:
                    f.write(html_content)


def GenerateHtmlReport(artefact, artefact_file, data_header, data_rows, html_template='body_artefact.htmll', allow_html = False):

    resource_base_html = resource_path('scripts\\html_templates', 'base.html')
    template_loader = FileSystemLoader(searchpath = os.path.dirname(resource_base_html))
    # autoescape HTML characters for security.
    env = Environment(
            loader = template_loader,
            autoescape = select_autoescape(['html', 'xml'])
    )

    # Create a unique ID to match the artefact page with the active navigation bar artefact item
    unique_id = str(uuid.uuid4())

    # Context data to pass to the HTML engine.
    context = {
        'version': aleapp_version,
        'title': f'{artefact.name} report',
        'unique_id': unique_id,
        'artefact': {
            'category': artefact.category,
            'name': artefact.name,
            'reference': artefact.artefact_reference,
            'files_found': artefact.files_found,
            'artefact_file': artefact_file,
            'data': {
                'allow_html': allow_html,
                'headers': data_header,
                'rows': data_rows
            }
        }
    }

    template = env.get_template('body_artefact.html')
    html_content = template.render(context = context)

    # Create HTML Temp folder
    temp_html_folder = os.path.join(artefact.report_folder, 'HTML Reports - Temp')
    os.makedirs(temp_html_folder, exist_ok = True)

    output_path = os.path.join(temp_html_folder, f'artefact_{artefact.name}.temphtml')
    report_path = get_next_unused_name(output_path)
    with open(report_path, mode = 'w', encoding = 'utf-8') as f:
        f.write(html_content)

    # Get the new unused file name for the navbar
    generated_file, _ = os.path.splitext(os.path.basename(report_path))

    # Append to a list for the navigation bar generation.
    GeneratedHtmlReports.setdefault(artefact.category, []).append({
        'name': generated_file.replace('artefact_',''),
        'unique_id': unique_id,
        'icon': artefact.icon,
        'file_name': f'{generated_file}.html',
    })


def resource_path(relative_path: str, file_name: str = ''):
    """
    Get absolute path to resource, works for both in IDE and for PyInstaller
    PyInstaller creates a temp folder and stores path in sys._MEIPASS
    C:/Users/Jamie/AppData/Local/Temp/_MEI###### (where # are digits)
    In IDE, the path is os.path.join(base_path, relative_path, file_name)
    Search in Dev path first, then MEIPASS for the compiled files.
    """

    # Developer folder
    base_path = os.path.abspath(".")
    dev_file_path = os.path.join(base_path, relative_path, file_name)

    if os.path.exists(dev_file_path):
        return dev_file_path

    # Portable Executable temporary folder.
    base_path = sys._MEIPASS
    file_path = os.path.join(base_path, relative_path, file_name)

    if os.path.exists(file_path):
        return file_path
    return None


class ArtifactHtmlReport:

    def __init__(self, artifact_name, artifact_category = ''):
        self.report_file = None
        self.report_file_path = ''
        self.script_code = ''
        self.artifact_name = artifact_name
        self.artifact_category = artifact_category  # unused



    def __del__(self):
        if self.report_file:
            self.end_artifact_report()

    def start_artifact_report(self, report_folder, artifact_file_name, artifact_description = ''):
        '''Creates the report HTML file and writes the artifact name as a heading'''
        self.report_file = open(os.path.join(report_folder, f'{artifact_file_name}.temphtml'), 'w', encoding = 'utf8')
        self.report_file.write(page_header.format(f'ALEAPP - {self.artifact_name} report'))
        self.report_file.write(body_start.format(f'ALEAPP {aleapp_version}'))
        self.report_file.write(body_sidebar_setup)
        self.report_file.write(body_sidebar_dynamic_data_placeholder)  # placeholder for sidebar data
        self.report_file.write(body_sidebar_trailer)
        self.report_file.write(body_main_header)
        self.report_file.write(body_main_data_title.format(f'{self.artifact_name} report', artifact_description))
        self.report_file.write(body_spinner)  # Spinner till data finishes loading
        # self.report_file.write(body_infinite_loading_bar) # Not working!

    def add_script(self, script = ''):
        '''Adds a default script or the script supplied'''
        if script:
            self.script_code += script + nav_bar_script_footer
        else:
            self.script_code += default_responsive_table_script + nav_bar_script_footer

    def write_artifact_data_table(self, data_headers, data_list, source_path,
                                  write_total = True, write_location = True, html_escape = True,
                                  cols_repeated_at_bottom = True,
                                  table_responsive = True, table_style = '', table_id = 'dtBasicExample'):
        ''' Writes info about data, then writes the table to html file
            Parameters
            ----------
            data_headers   : List/Tuple of table column names

            data_list      : List/Tuple of lists/tuples which contain rows of data

            source_path    : Source path of data

            write_total    : Toggles whether to write out a line of total rows written

            write_location : Toggles whether to write the location of data source

            html_escape    : If True (default), then html special characters are encoded

            cols_repeated_at_bottom : If True (default), then col names are also at the bottom of the table

            table_responsive : If True (default), div class is table_responsive

            table_style    : Specify table style like "width: 100%;"

            table_id       : Specify an identifier string, which will be referenced in javascript
        '''
        if (not self.report_file):
            raise ValueError('Output report file is closed/unavailable!')

        num_entries = len(data_list)
        if write_total:
            self.write_minor_header(f'Total number of entries: {num_entries}', 'h6')
        if write_location:
            if is_platform_windows():
                source_path = source_path.replace('/', '\\')
            if source_path.startswith('\\\\?\\'):
                source_path = source_path[4:]
            self.write_lead_text(f'{self.artifact_name} located at: {source_path}')

        self.report_file.write('<br />')

        if table_responsive:
            self.report_file.write("<div class='table-responsive'>")

        table_head = '<table id="{}" class="table table-striped table-bordered table-xsm" cellspacing="0" {}>' \
                     '<thead>'.format(table_id, (f'style="{table_style}"') if table_style else '')
        self.report_file.write(table_head)
        self.report_file.write(
            '<tr>' + ''.join(('<th class="th-sm">{}</th>'.format(html.escape(str(x))) for x in data_headers)) + '</tr>')
        self.report_file.write('</thead><tbody>')

        if html_escape:
            for row in data_list:
                self.report_file.write('<tr>' + ''.join(
                        ('<td>{}</td>'.format(html.escape(str(x) if x is not None else '')) for x in row)) + '</tr>')
        else:
            for row in data_list:
                self.report_file.write(
                    '<tr>' + ''.join(('<td>{}</td>'.format(str(x) if x is not None else '') for x in row)) + '</tr>')

        self.report_file.write('</tbody>')
        if cols_repeated_at_bottom:
            self.report_file.write('<tfoot><tr>' + ''.join(
                    ('<th>{}</th>'.format(html.escape(str(x))) for x in data_headers)) + '</tr></tfoot>')
        self.report_file.write('</table>')
        if table_responsive:
            self.report_file.write("</div>")

    def add_section_heading(self, heading, size = 'h2'):
        heading = html.escape(heading)
        data = '<div class="d-flex justify-content-between flex-wrap flex-md-nowrap align-items-center pt-3 pb-2 mb-3 border-bottom">' \
               '    <{0} class="{0}">{1}</{0}>' \
               '</div>'
        self.report_file.write(data.format(size, heading))

    def write_minor_header(self, heading, heading_tag = ''):
        heading = html.escape(heading)
        if heading_tag:
            self.report_file.write(f'<{heading_tag}>{heading}</{heading_tag}>')
        else:
            self.report_file.write(f'<h3 class="h3">{heading}</h3>')

    def write_lead_text(self, text):
        self.report_file.write(f'<p class="lead">{text}</p>')

    def write_raw_html(self, code):
        self.report_file.write(code)

    def end_artifact_report(self):
        if self.report_file:
            self.report_file.write(body_main_trailer + body_end + self.script_code + page_footer)
            self.report_file.close()
            self.report_file = None

# class ArtifactHtmlReport:
#
#     def __init__(self, artifact_name, artifact_category=''):
#         self.report_file = None
#         self.report_file_path = ''
#         self.script_code = ''
#         self.artifact_name = artifact_name
#         self.artifact_category = artifact_category # unused
#
#     def __del__(self):
#         if self.report_file:
#             self.end_artifact_report()
#
#     def start_artifact_report(self, report_folder, artifact_file_name, artifact_description=''):
#         '''Creates the report HTML file and writes the artifact name as a heading'''
#         self.report_file = open(os.path.join(report_folder, f'{artifact_file_name}.temphtml'), 'w', encoding='utf8')
#         self.report_file.write(page_header.format(f'ALEAPP - {self.artifact_name} report'))
#         self.report_file.write(body_start.format(f'ALEAPP {aleapp_version}'))
#         self.report_file.write(body_sidebar_setup)
#         self.report_file.write(body_sidebar_dynamic_data_placeholder) # placeholder for sidebar data
#         self.report_file.write(body_sidebar_trailer)
#         self.report_file.write(body_main_header)
#         self.report_file.write(body_main_data_title.format(f'{self.artifact_name} report', artifact_description))
#         self.report_file.write(body_spinner) # Spinner till data finishes loading
#         #self.report_file.write(body_infinite_loading_bar) # Not working!
#
#     def add_script(self, script=''):
#         '''Adds a default script or the script supplied'''
#         if script:
#             self.script_code += script + nav_bar_script_footer
#         else:
#             self.script_code += default_responsive_table_script + nav_bar_script_footer
#
#     def write_artifact_data_table(self, data_headers, data_list, source_path,
#             write_total=True, write_location=True, html_escape=True, cols_repeated_at_bottom=True,
#             table_responsive=True, table_style='', table_id='dtBasicExample'):
#         ''' Writes info about data, then writes the table to html file
#             Parameters
#             ----------
#             data_headers   : List/Tuple of table column names
#
#             data_list      : List/Tuple of lists/tuples which contain rows of data
#
#             source_path    : Source path of data
#
#             write_total    : Toggles whether to write out a line of total rows written
#
#             write_location : Toggles whether to write the location of data source
#
#             html_escape    : If True (default), then html special characters are encoded
#
#             cols_repeated_at_bottom : If True (default), then col names are also at the bottom of the table
#
#             table_responsive : If True (default), div class is table_responsive
#
#             table_style    : Specify table style like "width: 100%;"
#
#             table_id       : Specify an identifier string, which will be referenced in javascript
#         '''
#         if (not self.report_file):
#             raise ValueError('Output report file is closed/unavailable!')
#
#         num_entries = len(data_list)
#         if write_total:
#             self.write_minor_header(f'Total number of entries: {num_entries}', 'h6')
#         if write_location:
#             if is_platform_windows():
#                 source_path = source_path.replace('/', '\\')
#             if source_path.startswith('\\\\?\\'):
#                 source_path = source_path[4:]
#             self.write_lead_text(f'{self.artifact_name} located at: {source_path}')
#
#         self.report_file.write('<br />')
#
#         if table_responsive:
#             self.report_file.write("<div class='table-responsive'>")
#
#         table_head = '<table id="{}" class="table table-striped table-bordered table-xsm" cellspacing="0" {}>'\
#                      '<thead>'.format(table_id, (f'style="{table_style}"') if table_style else '')
#         self.report_file.write(table_head)
#         self.report_file.write('<tr>' + ''.join( ('<th class="th-sm">{}</th>'.format(html.escape(str(x))) for x in data_headers) ) + '</tr>')
#         self.report_file.write('</thead><tbody>')
#
#         if html_escape:
#             for row in data_list:
#                 self.report_file.write('<tr>' + ''.join( ('<td>{}</td>'.format(html.escape(str(x) if x is not None else '')) for x in row) ) + '</tr>')
#         else:
#             for row in data_list:
#                 self.report_file.write('<tr>' + ''.join( ('<td>{}</td>'.format(str(x) if x is not None else '') for x in row) ) + '</tr>')
#
#         self.report_file.write('</tbody>')
#         if cols_repeated_at_bottom:
#             self.report_file.write('<tfoot><tr>' + ''.join( ('<th>{}</th>'.format(html.escape(str(x))) for x in data_headers) ) + '</tr></tfoot>')
#         self.report_file.write('</table>')
#         if table_responsive:
#             self.report_file.write("</div>")
#
#     def add_section_heading(self, heading, size='h2'):
#         heading = html.escape(heading)
#         data = '<div class="d-flex justify-content-between flex-wrap flex-md-nowrap align-items-center pt-3 pb-2 mb-3 border-bottom">'\
#                 '    <{0} class="{0}">{1}</{0}>'\
#                 '</div>'
#         self.report_file.write(data.format(size, heading))
#
#     def write_minor_header(self, heading, heading_tag=''):
#         heading = html.escape(heading)
#         if heading_tag:
#             self.report_file.write(f'<{heading_tag}>{heading}</{heading_tag}>')
#         else:
#             self.report_file.write(f'<h3 class="h3">{heading}</h3>')
#
#     def write_lead_text(self, text):
#         self.report_file.write(f'<p class="lead">{text}</p>')
#
#     def write_raw_html(self, code):
#         self.report_file.write(code)
#
#     def end_artifact_report(self):
#         if self.report_file:
#             self.report_file.write(body_main_trailer + body_end + self.script_code + page_footer)
#             self.report_file.close()
#             self.report_file = None
#
