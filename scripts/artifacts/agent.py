import sqlite3
import textwrap

from scripts.artifact_report import ArtifactHtmlReport
from scripts.ilapfuncs import logfunc, tsv, is_platform_windows, open_sqlite_db_readonly

def get_agent(files_found, report_folder, seeker, wrap_text):
    
    for file_found in files_found:
        file_found = str(file_found)
        if not file_found.endswith('agent_mmssms.db'):
            continue # Skip all other files
        
        db = open_sqlite_db_readonly(file_found)
        cursor = db.cursor()
        cursor.execute('''
        SELECT 
            [mmssms].[address] AS [Participants], 
            [mmssms].[date] AS [Original Transmit Date/Time - UTC (yyyy-mm-dd)], 
            (CASE WHEN EXISTS (SELECT 1
            FROM   [data] [d2]
            WHERE  [d2].[_id] = [d1].[_id] AND [d2].[rowid] > [d1].[rowid]) THEN '1234' ELSE [mmssms].[body] END) AS [Message], 
            [d1].[attachment_type] AS [MIME Type], 
            [d1].[attachment_data] AS [Attachment], 
            [mmssms].[thread_id] AS [_ThreadID], 
            [mmssms].[type] AS [Message Status], 
            [mmssms].[rowid], 
            [d1].[rowid]
        FROM   [mmssms]
            LEFT OUTER JOIN [data] [d1] ON [d1].[_id] = [mmssms].[_id]
                AND [d1].[thread_id] = [mmssms].[thread_id];
        ''')
    
        all_rows = cursor.fetchall()
        usageentries = len(all_rows)
    if usageentries > 0:
        report = ArtifactHtmlReport('Agent Messages')
        report.start_artifact_report(report_folder, 'Agent Messages')
        report.add_script()
        data_headers = ('Participants','Original Transmit Date','Message','Mime','Thread ID', 'Message Status' )
        data_list = []
        for row in all_rows:
            data_list.append((row[0],row[1],row[2],row[3],row[5],row[6]))

        report.write_artifact_data_table(data_headers, data_list, file_found)
        report.end_artifact_report()
        
        tsvname = f'Agent Messages'
        tsv(report_folder, data_headers, data_list, tsvname)
    else:
        logfunc('Agent Messages data available')
    
    db.close()
    return

