import argparse
import scripts.report as report

from scripts.search_files import *
from scripts.ilapfuncs import *
from scripts.ilap_artifacts import *
from scripts.version_info import aleapp_version
from time import process_time, gmtime, strftime
from scripts.plugin_manager import PluginManager


def main():
    parser = argparse.ArgumentParser(description='ALEAPP: Android Logs, Events, and Protobuf Parser.')
    parser.add_argument('-t', choices=['fs', 'tar', 'zip', 'gz'], required=False, type=str.lower, action='store', help='Input type (fs = extracted to file system folder).')
    parser.add_argument('-o', '--output_path', required=False, action='store', help='Output folder path.')
    parser.add_argument('-i', '--input_path', required=False, action='store', help='Path to input file/folder.')
    parser.add_argument('-p', '--artifact_paths', required=False, action='store_true', help='Text file list of artifact paths.')
    parser.add_argument('-w', '--wrap_text', required=False, action='store_false', help='Do not wrap text for output of data files.')

    args = parser.parse_args()
    
    if args.artifact_paths:
        print('Artifact path list generation started.')
        print('')
        with open('path_list.txt', 'a') as paths:
            for plugin in PluginManager('scripts.artifacts').plugins:
                for path_filter in plugin.path_filters:
                    paths.write(f'{path_filter}\n')
                    print(path_filter)
        print('')
        print('Artifact path list generation completed.')
        return

    input_path = args.input_path
    extracttype = args.t

    if args.wrap_text is None:
        wrap_text = True
    else:
        wrap_text = args.wrap_text

    if args.output_path is None:
        parser.error('No OUTPUT folder path provided.')
        return
    else:
        output_path = os.path.abspath(args.output_path)

    if output_path is None:
        parser.error('No OUTPUT folder selected. Run the program again.')
        return

    if input_path is None:
        parser.error('No INPUT file or folder selected. Run the program again.')
        return

    if args.t is None:
        parser.error('No INPUT FILE TYPE selected. Run the program again.')
        return

    if not os.path.exists(input_path):
        parser.error('INPUT file/folder does not exist! Run the program again.')
        return

    if not os.path.exists(output_path):
        parser.error('OUTPUT folder does not exist! Run the program again.')
        return

    # Long (260 chars) file path names cause issues in Windows: Fixed with a conversion.
    if is_platform_windows():
        if input_path[1] == ':' and extracttype == 'fs':
            input_path = convert_to_long_path(input_path)
        if output_path[1] == ':':
            output_path = convert_to_long_path(output_path)

    out_params = OutputParameters(output_path)

    crunch_artifacts(extracttype, input_path, out_params, 1, wrap_text)


def crunch_artifacts( extracttype, input_path, out_params, ratio, wrap_text):
    start = process_time()

    logfunc('Processing started. Please wait. This may take a few minutes...')

    logfunc('\n--------------------------------------------------------------------------------------')
    logfunc(f'ALEAPP v{aleapp_version}: Android Logs, Events, and Protobuf Parser.')
    logfunc('Objective: Triage Android Full System Extractions.')
    logfunc('By: Alexis Brignoni | @AlexisBrignoni | abrignoni.com')
    logfunc('By: Yogesh Khatri   | @SwiftForensics | swiftforensics.com')

    seeker = None
    try:
        if extracttype == 'fs':
            seeker = FileSeekerDir(input_path)

        elif extracttype in ('tar', 'gz'):
            seeker = FileSeekerTar(input_path, out_params.temp_folder)

        elif extracttype == 'zip':
            seeker = FileSeekerZip(input_path, out_params.temp_folder)

        else:
            logfunc('Error on argument -o (input type).')
            return False
    except Exception as ex:
        logfunc('Had an exception in Seeker - see details below. Terminating Program!')
        logfunc(traceback.format_exc())
        return False

    plugin_manager = PluginManager('scripts.artifacts', plugins_in_debug_only = False)

    # Now ready to run
    logfunc(f'Artifact categories to parse: {len(plugin_manager.plugins)}')
    logfunc(f'File/Directory selected: {input_path}')
    logfunc('\n--------------------------------------------------------------------------------------')

    log = open(os.path.join(out_params.report_folder_base, 'Script Logs', 'ProcessedFilesLog.html'), 'w+', encoding='utf8')
    log.write(f'Extraction/Path selected: {input_path}<br><br>')
    log.close()

    categories_searched = 0

    # Process all the artefqcts.
    for plugin in plugin_manager.plugins:
        plugin.seeker = seeker
        plugin.wrap_text = wrap_text
        plugin.search_for_artefacts()
        plugin.process_artefact(out_params.report_folder_base)

        categories_searched += 1
        GuiWindow.SetProgressBar(categories_searched * ratio)

    logfunc('')
    logfunc('Processes completed.')
    end = process_time()
    run_time_secs = end - start
    run_time_HMS = strftime('%H:%M:%S', gmtime(run_time_secs))
    logfunc(f'Processing time = {run_time_HMS}')

    logfunc('')
    logfunc('Report generation started.')
    # remove the \\?\ prefix we added to input and output paths, so it does not reflect in report
    if is_platform_windows(): 
        if out_params.report_folder_base.startswith('\\\\?\\'):
            out_params.report_folder_base = out_params.report_folder_base[4:]
        if input_path.startswith('\\\\?\\'):
            input_path = input_path[4:]
    report.generate_report(out_params.report_folder_base, run_time_secs, run_time_HMS, extracttype, input_path)
    logfunc('Report Generation Completed.')
    logfunc('')
    logfunc(f'Report location: {out_params.report_folder_base}')
    return True


if __name__ == '__main__':
    main()
