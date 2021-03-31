from scripts.plugin_base import ArtefactPlugin
from scripts.artifact_report import ArtifactHtmlReport
from scripts.ilapfuncs import logfunc, tsv
from scripts import artifact_report

class BuildPlugin(ArtefactPlugin):
    """
    This plugin gets the build information.
    """

    def __init__(self):
        super().__init__()
        self.author = 'Unknown'
        self.author_email = ''
        self.author_url = ''

        self.category = 'Device Info'
        self.name = 'Build Info'
        self.description = 'Parses device build information.'

        self.artefact_reference = 'Build information of the acquired device.'  # Description on what the artefact is.
        self.path_filters = ['**/vendor/build.prop']  # Collection of regex search filters to locate an artefact.
        self.icon = 'terminal'  # feathricon for report.

    def _processor(self) -> bool:
        data_list = []
        file_found = str(self.files_found[0])
        with open(file_found, "r") as f:
            for line in f:
                splits = line.split('=')
                if splits[0] == 'ro.product.vendor.manufacturer':
                    key = 'Manufacturer'
                    value = splits[1]
                elif splits[0] == 'ro.product.vendor.brand':
                    key = 'Brand'
                    value = splits[1]
                    data_list.append((key, value))
                elif splits[0] == 'ro.product.vendor.model':
                    key = 'Model'
                    value = splits[1]
                    data_list.append((key, value))
                elif splits[0] == 'ro.product.vendor.device':
                    key = 'Device'
                    value = splits[1]
                    data_list.append((key, value))
                elif splits[0] == 'ro.vendor.build.version.release':
                    key = 'Android Version'
                    value = splits[1]
                    data_list.append((key, value))
                elif splits[0] == 'ro.vendor.build.version.sdk':
                    key = 'SDK'
                    value = splits[1]
                    data_list.append((key, value))
                elif splits[0] == 'ro.system.build.version.release':
                    key = ''
                    value = splits[1]
                    data_list.append((key, value))
                elif splits[0] == 'ro.system.build.version.release':
                    key = ''
                    value = splits[1]
                    data_list.append((key, value))

        itemqty = len(data_list)
        if itemqty > 0:

            data_headers = ('Key', 'Value')
            artifact_report.GenerateHtmlReport(self, file_found, data_headers, data_list)

            tsv(self.report_folder, data_headers, data_list, self.full_name())
        else:
            logfunc(f'No Build Info data available')

        return True
