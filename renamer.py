"""
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
import argparse

version = '0.2.0'


def apply_names(input_filename, core_list_filename, **kwargs):
    start_time = timeit.default_timer()

    if 'kwargs' in kwargs:
        kwargs = kwargs['kwargs']
        if kwargs['verbose']:
            print('kwargs dict passed as dict value.')

    ### Pull out all the options parameters
    header_row = kwargs['headerrow'] if 'headerrow' in kwargs else 0
    units_row = kwargs['unitsrow'] if 'unitsrow' in kwargs else 1
    start_row = kwargs['startrow'] if 'startrow' in kwargs else 2
    verbose = kwargs['verbose']
    
    if verbose:
        print('kwargs:',kwargs)

    ### Import the data
    mscl_data = []
    section_list = []

    with open(input_filename, 'r', encoding='utf-8-sig') as f:
        mscl_data = [r.strip().split(',') for r in f.read().splitlines()]


    if 'sectioncolumn' in kwargs:
        section_column = kwargs['sectioncolumn']
        if verbose:
            print('Section column passed at command line:',section_column)
    else:
        if 'SECT NUM' in mscl_data[0]:
            section_column = mscl_data[0].index('SECT NUM')
            if verbose:
                print('Section number column found in file with column name \'SECT NUM\':',section_column)
        elif 'Section' in mscl_data[0]:
            section_column = mscl_data[0].index('Section')
            if verbose:
                print('Section number column found in file with column name \'Section\':',section_column)
        else:
            print('ERROR: Cannot find section number column. Please change section number column name to \'Section\' or \'SECT NUM\'.')
            exit(1)

    if 'depthcolumn' in kwargs:
        section_depth_column = kwargs['depthcolumn']
        if verbose:
            print('Section depth column passed at command line:',section_depth_column)
    else:
        if 'Section Depth' in mscl_data[0]:
            section_depth_column = mscl_data[0].index('Section Depth')
            if verbose:
                print('Section depth column found in file with column name \'Section Depth\':',section_depth_column)
        elif 'SECT DEPTH' in mscl_data[0]:
            section_depth_column = mscl_data[0].index('SECT DEPTH')
            if verbose:
                print('Section depth column found in file with column name \'SECT DEPTH\':',section_depth_column)
        else:
            print('ERROR: Cannot find section depth column. Please change section depth column name to \'Section Depth\' or \'SECT DEPTH\'.')
            exit(1)

    # Build the section list
    with open(core_list_filename, 'r', encoding='utf-8-sig') as f:
        rows = f.read().splitlines()
        section_list = [[int(a), b] for a, b in [r.split(',') for r in rows]]

    # Add the filepart_section notation field to the section log
    nSections = 1
    for i, row in enumerate(section_list):
        if i == 0:
            row.append('1_' + str(section_list[i][0]))
        elif i > 0:
            if section_list[i][0] <= section_list[i-1][0]:
                nSections += 1
            row.append(str(nSections) + '_' + str(section_list[i][0]))

    # Build a dictionary for lookup from the list
    sectionDict = {section[2]: section[1] for section in section_list}

    # Add the part_section notation field to the mscl data
    nSections = 1
    for i, row in enumerate(mscl_data):
        if i == header_row:
            row.append('Part_Section')
        elif i == units_row:
            row.append('')
        elif i == start_row:
            row.append(str(nSections) + '_' + mscl_data[i][section_column])
        elif i > start_row:
            if int(mscl_data[i][section_column]) < int(mscl_data[i-1][section_column]):
                nSections += 1
            elif ((int(mscl_data[i][section_column]) == int(mscl_data[i-1][section_column])) & (float(mscl_data[i][section_depth_column]) < float(mscl_data[i-1][section_depth_column]))):
                nSections += 1
            row.append(str(nSections) + '_' + mscl_data[i][section_column])
        else:
            if verbose:
                print('Ignored row {0} (not header or units row and before start row):\n{1}'.format(i,row))


    ### Build the export lists
    matched_data = []
    unmatched_data = []

    # Build the export lists, replacing the geotek file section number with the
    # coreID and removing the extra part_section column if the row was matched.
    for row in mscl_data[start_row:]:
        if row[-1] in sectionDict.keys():
            row[section_column] = sectionDict[row[-1]]
            matched_data.append(row[:-1])
        else:
            unmatched_data.append(row)
    
    # Build export names
    matched_filename = kwargs['outputfilename'] if 'outputfilename' in kwargs else input_filename.split('.')[0] + '_coreID.csv'
    unmatched_filename = kwargs['unmatchedfilename'] if 'unmatchedfilename' in kwargs else input_filename.split('.')[0] + '_unmatched.csv'

    ### Export matched data
    with open(matched_filename, 'w', encoding='utf-8-sig') as f:
        f.write(','.join(mscl_data[header_row][:-1])+'\n')
        f.write(','.join(mscl_data[units_row][:-1])+'\n')
        for r in matched_data:
            f.write(','.join(r)+'\n')

    ### Export unmatched data
    if len(unmatched_data) != 0:
        with open(unmatched_filename, 'w', encoding='utf-8-sig') as f:
            f.write(','.join(mscl_data[header_row])+'\n')
            f.write(','.join(mscl_data[units_row])+'\n')
            for r in unmatched_data:
                f.write(','.join(r)+'\n')
    
    ### Reporting stuff
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

    print(len(matched_data),'rows had section names assigned (' + matched_filename + ').')
    print('There were no unmatched rows.' if len(unmatched_data) == start_row else 'There were ' + str(len(unmatched_data)) + ' unmatched rows (' + unmatched_filename + ').')
    if verbose:
        print('Completed in',round((end_time - start_time),2),'seconds.')    


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Apply coreIDs to the output from Geotek MSCL software.')
    parser.add_argument('input_filename', type=str, help='Name of input file.')
    parser.add_argument('-c', '--corelist', type=str, help='Name of the core list file.')
    parser.add_argument('-s', '--sectioncolumn', type=int, help='Column number the section numbers are in (count starts at 0).')
    parser.add_argument('-o', '--outputfilename', type=str, help='Name of the output file.')
    parser.add_argument('-n', '--unmatchedfilename', type=str, help='Name of the output file for unmatched data.')
    parser.add_argument('-d', '--depthcolumn', type=int, help='Column number the section depths are in (count starts at 0).')
    parser.add_argument('-r', '--startrow', type=int, help='Row number the MSCL data begins (count starts at 0).')
    parser.add_argument('-t', '--headerrow', type=int, help='Row number the headers are on (count starts at 0).')
    parser.add_argument('-u', '--unitsrow', type=int, help='Row number the units are on (count starts at 0).')
    parser.add_argument('-v', '--verbose', action='store_true', help='Increase verbosity.')

    args = parser.parse_args()

    if args.corelist:
        core_list_filename = args.corelist
    elif os.path.isfile('corelist.csv'):
        core_list_filename = 'corelist.csv'
    else:
        print('A core list file needs to be specified (e.g. python renamer.py -c PRJ_core_list.csv).')
        print('Alternatively, a file named corelist.csv must exist in the same directory.')
        print('The core list should be a csv file with the following format: sectionNumber,coreID')
        print('e.g.: 1,PROJ-LAK17-1A-1P-1-A\n      2,PROJ-LAK17-1A-2B-1-A\n      3,PROJ-LAK17-1A-3B-1-A\n      1,PROJ-LAK17-2A-1P-1-A\n      2,PROJ-LAK17-2A-1P-2-A')
        exit(1)

    # Build dict of specified optional parameters to pass to function
    # Is there a best practice to handle this? seems pretty hacky
    argsDict = {k:v for k,v in vars(args).items() if v is not None}

    apply_names(args.input_filename, core_list_filename, kwargs=argsDict)
