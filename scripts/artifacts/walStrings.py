import os
import re
import string

from pathlib import Path
from scripts.plugin_base import ArtefactPlugin
from scripts.artifact_report import ArtifactHtmlReport
from scripts import artifact_report

class WalStringsPlugin(ArtefactPlugin):
    """
    """

    def __init__(self):
        super().__init__()
        self.author = 'Unknown'
        self.author_email = ''
        self.author_url = ''

        self.name = 'SQLite Journaling'
        self.description = ''

        self.artefact_reference = 'ASCII strings extracted from SQLite journal and WAL files.'  # Description on what the artefact is.
        self.path_filters = [
            '**/*-wal',
            '**/*-journal'
        ]  # Collection of regex search filters to locate an artefact.
        self.icon = 'list'  # feathricon for report.

    def _processor(self) -> bool:

        control_chars = ''.join(map(chr, range(0,32))) + ''.join(map(chr, range(127,160)))
        not_control_char_re = re.compile(f'[^{control_chars}]' + '{4,}')
        # If  we only want ascii, use 'ascii_chars_re' below
        printable_chars_for_re = string.printable.replace('\\', '\\\\').replace('[', '\\[').replace(']', '\\]')
        ascii_chars_re = re.compile(f'[{printable_chars_for_re}]' + '{4,}')

        x = 1
        data_list = []
        for file_found in self.files_found:
            filesize = Path(file_found).stat().st_size
            if filesize == 0:
                continue

            journalName = os.path.basename(file_found)
            outputpath = os.path.join(self.report_folder, str(x) + '_' + journalName + '.txt') # name of file in txt

            level2, level1 = (os.path.split(outputpath))
            level2 = (os.path.split(level2)[1])
            final = level2 + '/' + level1

            unique_items = set() # For deduplication of strings found
            with open(outputpath, 'w') as g:
                with open(file_found, errors="ignore") as f:  # Python 3.x
                    data = f.read()
                    #for match in not_control_char_re.finditer(data): # This gets all unicode chars, can include lot of garbage if you only care about English, will miss out other languages
                    for match in ascii_chars_re.finditer(data): # Matches ONLY Ascii (old behavior) , good if you only care about English
                        if match.group() not in unique_items:
                            g.write(match.group())
                            g.write('\n')
                            unique_items.add(match.group())
                g.close()

            if unique_items:
                out = (f'<a href="{final}" style = "color:blue" target="_blank">{journalName}</a>')
                data_list.append((out, file_found))
            else:
                try:
                    os.remove(outputpath) # delete empty file
                except OSError:
                    pass
            x = x + 1

        data_headers = ('Report', 'Location')
        artifact_report.GenerateHtmlReport(self, '', data_headers, data_list, allow_html = True)

        return True
