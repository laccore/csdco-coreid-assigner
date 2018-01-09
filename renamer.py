"""
Both pandas and numpy could do this orders of magnitude more efficiently, but as
this will be used in the field by people not familiar with python, it's using
only built-in libraries.

Arguments: input_filename.csv [corelist.csv]

You can specify a core list file name, but if none is specified it looks for a file
in the same directory named corelist.csv to use. It will fail if no file is 
specified and corelist.csv doesn't exist.

Examples:
    $ python3 renamer.py DCH_MSCL_raw.csv
    $ python3 renamer.py YLAKE_XYZ.csv YLAKE_core_list.csv

Incorrect command line usage will print an explanation.
"""

import sys
import os.path
import timeit

version = '0.2.0'

start_time = timeit.default_timer()

def apply_names(input_filename, matched_filename, unmatched_filename):
    mscl_data = []
    sectionList = []

    with open(input_filename, 'r') as f:
        mscl_data = [r.split(',') for r in f.read().splitlines()]

    # Ideally with a GUI these would be fields that could be entered
    start_row = 2

    # handle failure better
    if 'SECT NUM' in mscl_data[0]:
        section_column = mscl_data[0].index('SECT NUM')
    elif 'Section' in mscl_data[0]:
        section_column = mscl_data[0].index('Section')
    else:
        print('ERROR: Cannot find section number column. Please change section number column name to \'Section\' or \'SECT NUM\'.')
        exit(1)

    # handle failure better
    if 'Section Depth' in mscl_data[0]:
        section_depth_column = mscl_data[0].index('Section Depth')
    elif 'SECT DEPTH' in mscl_data[0]:
        section_depth_column = mscl_data[0].index('SECT DEPTH')
    else:
        print('ERROR: Cannot find section depth column. Please change section depth column name to \'Section Depth\' or \'SECT DEPTH\'.')
        exit(1)

    # Build the section list
    with open(core_list_filename, 'r') as f:
        rows = f.read().splitlines()
        sectionList = [[int(a), b] for a, b in [r.split(',') for r in rows]]

    # Add the filepart_section notation field to the section log
    nSections = 1
    for i, row in enumerate(sectionList):
        if i == 0:
            row.append('1_' + str(sectionList[i][0]))
        elif i > 0:
            if sectionList[i][0] <= sectionList[i-1][0]:
                nSections += 1
            row.append(str(nSections) + '_' + str(sectionList[i][0]))

    # Build a dictionary for lookup from the list
    sectionDict = {section[2]: section[1] for section in sectionList}

    # Add the part_section notation field to the mscl data
    nSections = 1
    for i, row in enumerate(mscl_data):
        if i == 0:
            row.append('Part_Section')
        elif i < start_row:
            row.append('')
        elif i == start_row:
            row.append(str(nSections) + '_' + mscl_data[i][section_column])
        else:
            if int(mscl_data[i][section_column]) < int(mscl_data[i-1][section_column]):
                nSections += 1
            elif ((int(mscl_data[i][section_column]) == int(mscl_data[i-1][section_column])) & (float(mscl_data[i][section_depth_column]) < float(mscl_data[i-1][section_depth_column]))):
                nSections += 1
            row.append(str(nSections) + '_' + mscl_data[i][section_column])

    # These will be the lists we export from
    matched_data = []
    unmatched_data = []

    # Copy headers
    for row in mscl_data[:start_row]:
        matched_data.append(row[:-1])
        unmatched_data.append(row)

    # Build the export lists, replacing the section# with the name and removing
    # the extra part_section column if the row was matched
    for row in mscl_data[start_row:]:
        # Does the part_section key exist in the dict?
        if row[-1] in sectionDict.keys():
            row[section_column] = sectionDict[row[-1]]
            matched_data.append(row[:-1])
        else:
            unmatched_data.append(row)
    

    # Export matched data
    with open(matched_filename, 'w') as f:
        for r in matched_data:
            f.write(','.join(r)+'\n')

    # Export unmatched data
    if len(unmatched_data) > start_row:
        with open(unmatched_filename, 'w') as f:
            for r in unmatched_data:
                f.write(','.join(r)+'\n')
    
    # Reporting stuff
    # Create a set to check unique cores names
    named_set = set()

    for row in matched_data[start_row:]:
        named_set.add(row[section_column])

    core_name_list = list(sectionDict.values())
    for core_name in list(set(core_name_list)):
        core_name_count = core_name_list.count(core_name)
        if core_name_count > 1:
            print('WARNING: Core ' + core_name + ' appears in ' + core_list_filename + ' ' + str(core_name_count) + ' times.')


    count_diff = len(set(sectionDict.values())) - len(named_set)
    if (count_diff > 0):
        err = 'WARNING: Not all cores in ' + core_list_filename + ' were used.\n'
        err += 'The following ' + str(count_diff) + ' core ' + ('names were' if count_diff != 1 else 'name was') + ' not used:\n'
        for v in list(set(sectionDict.values())):
            if (v not in named_set):
                err += v + '\n'
        print(err)
        

    end_time = timeit.default_timer()

    print(len(matched_data)-start_row,'rows had section names assigned (' + matched_filename + ').')
    print('There were no unmatched rows.' if len(unmatched_data) == start_row else 'There were ' + str(len(unmatched_data)-2) + ' unmatched rows (' + unmatched_filename + ').')
    print('Completed in',round((end_time - start_time),2),'seconds.')    


if __name__ == '__main__':
    # If zero or more than 2 parameters are passed, print correct usage and exit.
    if len(sys.argv) > 3 or len(sys.argv) == 1:
        print('Usage: python renamer.py <MSCL file.csv> (<core list.csv>)')
        exit(1)
    
    # Find the core list
    # If core list not specified and corelist.csv doesn't exist, tell user it's needed and what it looks like
    if len(sys.argv) > 2:
        core_list_filename = sys.argv[2]
    elif os.path.isfile('corelist.csv'):
        core_list_filename = 'corelist.csv'
    else:
        print('A core list file needs to be specified as the last argument, or a file named corelist.csv must exist in the same directory.')
        print('The core list should be a csv file with the following format: sectionNumber,coreID')
        print('e.g.: 1,PROJ-LAK17-1A-1P-1-A\n      2,PROJ-LAK17-1A-2B-1-A\n      3,PROJ-LAK17-1A-3B-1-A\n      1,PROJ-LAK17-2A-1P-1-A\n      2,PROJ-LAK17-2A-1P-2-A')
        exit(1)

    # Build the various file names
    input_filename = sys.argv[1]
    matched_filename = input_filename[:len(input_filename)-12] + '.csv' if ('unnamed' in input_filename) else input_filename[:len(input_filename)-4] + '_sectionNames.csv'
    unmatched_filename = (input_filename[:len(input_filename)-12] if ('unnamed' in input_filename) else input_filename[:len(input_filename)-4]) + '_UNMATCHED.csv'

    apply_names(input_filename, matched_filename, unmatched_filename)
