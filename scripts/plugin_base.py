"""
Base class for an artefact plugin system.
"""
from scripts.ilapfuncs import *
from scripts import search_files
import os
import traceback


class ArtefactPlugin:
    """
    Base class that each artefact plugin must inherit from.

    Each plugin must:

        * Provide a name.
        * Provide a description.
        * Provide a path filter list.
        * Provide a feathericon for HTML report - https://feathericons.com/
        * Implement the process_artefact method.

    Addition classes/methods/modules may be added by the plugin author to further support the process_artefact.
    """

    def __init__(self):
        """
         Setup of artefact.
        """

        # Author Details
        self.author: str = 'Unknown Author'
        self.author_email: str = ''
        self.author_url: str = ''
        self.contributors: list = []  # List of names who helped in the artefact identification/parsing.

        # Artefact Details
        self.name: str = 'Unknown Plugin'  # Friendly plugin name.
        self.description: str = ''  # What does the plugin do.
        self.artefact_reference: str = ''  # Description on what the artefact is.
        self.path_filters: list = []  # Collection of regex search filters to locate an artefact.
        self.icon: str = ''  # feathricon for report.

        # Artefact Processing Details
        # Do not alter these in your plugin implementation. They are purely for reference in your processing implementation.
        self.files_found: list = []  # Collection of all the file paths that match self.path_filters.
        self.report_folder: str = ''  # Artefact report folder.
        self.seeker: search_files.FileSeekerBase = None  # Seeker object to search for additional files in the evidence.
        self.wrap_text: bool = True  # Determine if text should be wrapped on a new line.

        self.debug_mode: bool = False  # Determine if only this plugin should run. See plugin_manager.py[.plugins_in_debug_only]

    def process_artefact(self, report_folder_base: str) -> bool:
        """
        Processor wrapper.

        This prepares any temp folders, and wraps the plugins processor in a try/catch for safety.

        :param report_folder_base:
        :return:
        """
        logfunc()
        logfunc(f'Processing {self.name} artifact parser.')

        if not self.files_found:
            logfunc('No artefacts to parse.')
            return True

        slash = '\\' if is_platform_windows() else '/'

        self.report_folder = os.path.join(report_folder_base, self.name) + slash
        os.makedirs(self.report_folder, exist_ok = True)

        processor_success_status = False
        try:
            processor_success_status = self._processor()
        except Exception as ex:
            logfunc(f'Processing {self.name} artifacts had errors!')
            logfunc(f'Error was {ex}')
            logfunc(f'Exception Traceback: {traceback.format_exc()}')
            processor_success_status = False

        logfunc(f'{self.name} artifact completed {("successfully" if processor_success_status else "unsuccessfully")}.')

        return processor_success_status

    def _processor(self) -> bool:
        """
        Core processing method. This is where you implement your artefact parsing/processing.
        The plugin system will only call this method.

        This method is not to be called externally.

        :return: Bool - True on successful parse, False if errors occurred.
        """

        raise NotImplementedError(f'The plugin "{self.name}" ({__name__}) has not been implemented.')

    def search_for_artefacts(self):
        """
        Searches for artefacts among the seeker using the provided plugin's path_filters.

        :return:
        """

        logfunc()
        logfunc(f'Plugin "{self.name}" - Searching for artefacts.')
        for path_filter in self.path_filters:

            path_files_found = self.seeker.search(path_filter)

            if not path_files_found:
                logfunc(f'\tPlugin "{self.name}" with regex "{path_filter}" located no files.')
                continue

            self.files_found.extend(path_files_found)

            # Log all the files found with the path filter.
            for path_located in path_files_found:
                if path_located.startswith('\\\\?\\'):
                    path_located = path_located[4:]
                logfunc(f'\tPlugin "{self.name}" with regex "{path_filter}" located file "{path_located}"')

        logfunc(f'Plugin "{self.name}" found {len(self.files_found)} artefact(s).')
        logfunc(f'Plugin "{self.name}" - Search complete.')

    def __str__(self):
        return f'{self.name}'
