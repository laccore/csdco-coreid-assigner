"""
Both pandas and numpy could do this orders of magnitude more efficiently, but as
this will be used in the field by people not familiar with python, it's using
only built-in libraries.

Arguments: rawFileName.csv [corelist.csv]

You can specify a core list file name, but if none is specified it tries to use
corelist.csv. It will fail if corelist.csv doesn't exist and no file is specified.

Examples:
    $ python3 renamer.py DCH_MSCL_raw.csv
    $ python3 renamer.py YLAKE_XYZ.csv YLAKE_core_list.csv

Incorrect command line usage will print an explanation.
"""

import sys
import os.path
import timeit

version = '0.2.0'

start = timeit.default_timer()

def applyNames(rawFileName, matchedFileName, unmatchedFileName):
    msclData = []
    sectionList = []

    with open(rawFileName, 'r') as f:
        msclData = [r.split(',') for r in f.read().splitlines()]

    # Ideally with a GUI these would be fields that could be entered
    startRow = 2

    # handle failure better
    if 'SECT NUM' in msclData[0]:
        sectionColumn = msclData[0].index('SECT NUM')
    elif 'Section' in msclData[0]:
        sectionColumn = msclData[0].index('Section')
    else:
        print('ERROR: Cannot find section number column. Please change section number column name to \'Section\' or \'SECT NUM\'.')
        exit(-1)

    # handle failure better
    if 'Section Depth' in msclData[0]:
        sectionDepth = msclData[0].index('Section Depth')
    elif 'SECT DEPTH' in msclData[0]:
        sectionDepth = msclData[0].index('SECT DEPTH')
    else:
        print('ERROR: Cannot find section depth column. Please change section depth column name to \'Section Depth\' or \'SECT DEPTH\'.')
        exit(-1)

    # Build the section list
    with open(coreList, 'r') as f:
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
    for i, row in enumerate(msclData):
        if i == 0:
            row.append('Part_Section')
        elif i < startRow:
            row.append('')
        elif i == startRow:
            row.append(str(nSections) + '_' + msclData[i][sectionColumn])
        else:
            if int(msclData[i][sectionColumn]) < int(msclData[i-1][sectionColumn]):
                nSections += 1
            elif ((int(msclData[i][sectionColumn]) == int(msclData[i-1][sectionColumn])) & (float(msclData[i][sectionDepth]) < float(msclData[i-1][sectionDepth]))):
                nSections += 1
            row.append(str(nSections) + '_' + msclData[i][sectionColumn])

    # These will be the lists we export from
    matchedData = []
    unmatchedData = []

    # Copy headers
    for row in msclData[:startRow]:
        matchedData.append(row[:-1])
        unmatchedData.append(row)

    # Build the export lists, replacing the section# with the name and removing
    # the extra part_section column if the row was matched
    for row in msclData[startRow:]:
        # Does the part_section key exist in the dict?
        if row[-1] in sectionDict.keys():
            row[sectionColumn] = sectionDict[row[-1]]
            matchedData.append(row[:-1])
        else:
            unmatchedData.append(row)
    

    # Export matched data
    with open(matchedFileName, 'w') as f:
        for r in matchedData:
            f.write(','.join(r)+'\n')

    # Export unmatched data
    if len(unmatchedData) > startRow:
        with open(unmatchedFileName, 'w') as f:
            for r in unmatchedData:
                f.write(','.join(r)+'\n')
    
    # Reporting stuff
    # Create a set to check unique cores names
    namedSet = set()

    for row in matchedData[startRow:]:
        namedSet.add(row[sectionColumn])

    coreNameList = list(sectionDict.values())
    for cn in list(set(coreNameList)):
        cnc = coreNameList.count(cn)
        if cnc > 1:
            print('WARNING: Core ' + cn + ' appears in ' + coreList + ' ' + str(cnc) + ' times.')


    countDiff = len(set(sectionDict.values())) - len(namedSet)
    if (countDiff > 0):
        err = 'WARNING: Not all cores in ' + coreList + ' were used. '
        err = err + 'The following ' + str(countDiff) + ' core ' + ('names were' if countDiff != 1 else 'name was') + ' not used:'
        print(err)
        for v in list(set(sectionDict.values())):
            if (v not in namedSet):
                print(v)

    stop = timeit.default_timer()

    print(len(matchedData)-startRow,'rows had section names assigned (' + matchedFileName + ').')
    print('There were no unmatched rows.' if len(unmatchedData) == startRow else 'There were ' + str(len(unmatchedData)-2) + ' unmatched rows (' + unmatchedFileName + ').')
    print('Completed in',round((stop - start),2),'seconds.')    


if __name__ == '__main__':
    # If zero or more than 2 parameters are passed, print correct usage and exit.
    if len(sys.argv) > 3 or len(sys.argv) == 1:
        print('Usage: python renamer.py <MSCL file.csv> (<core list.csv>)')
        exit(-1)
    
    # Find the core list
    # If core list not specified and corelist.csv doesn't exist, tell user it's needed and what it looks like
    if len(sys.argv) > 2:
        coreList = sys.argv[2]
    elif os.path.isfile('corelist.csv'):
        coreList = 'corelist.csv'
    else:
        print('A core list file needs to be specified as the last argument, or a file named corelist.csv must exist in the same directory.')
        print('The core list should be a csv file with the following format: sectionNumber,coreID')
        print('e.g.: 1,PROJ-LAK17-1A-1P-1-A\n      2,PROJ-LAK17-1A-2B-1-A\n      3,PROJ-LAK17-1A-3B-1-A\n      1,PROJ-LAK17-2A-1P-1-A\n      2,PROJ-LAK17-2A-1P-2-A')
        exit(-1)

    # Build the various file names
    rawFileName = sys.argv[1]
    matchedFileName = rawFileName[:len(rawFileName)-12] + '.csv' if ('unnamed' in rawFileName) else rawFileName[:len(rawFileName)-4] + '_sectionNames.csv'
    unmatchedFileName = (rawFileName[:len(rawFileName)-12] if ('unnamed' in rawFileName) else rawFileName[:len(rawFileName)-4]) + '_UNMATCHED.csv'

    applyNames(rawFileName, matchedFileName, unmatchedFileName)
