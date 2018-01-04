"""
Both pandas and numpy could do this orders of magnitude more efficiently, but as
this will be used in the field by people not familiar with python, it's using
only built-in libraries.

Arguments: rawFileName.csv [corelist.csv]

You can specify a core list file name, but if none is specified it tries to use
corelist.csv. It will fail if corelist.csv doesn't exist and no file is specified.

Examples:
    $ python3 AssignSectionNames.py DCH_MSCL_raw.csv
    $ python3 AssignSectionNames.py YLAKE_XYZ.csv YLAKE_core_list.csv
"""


import sys
import os.path
import csv
import timeit

version = '0.1.0'
debug = 0

start = timeit.default_timer()


def applyNames(rawFileName, matchedFileName, unmatchedFileName):
    canRun = True
    
    msclData = []
    sectionList = []

    try:
        with open(rawFileName, 'r') as rawDataFile:
            fileReader = csv.reader(rawDataFile)
            for row in fileReader:
                if '\ufeff' in row[0]:
                    row[0] = row[0].replace('\ufeff','')
                msclData.append(row)
    except OSError as err:
        print("OS error: {0}".format(err))

    # Ideally with a GUI these would be fields that could be entered
    startRow = 2

    # handle failure better
    if 'SECT NUM' in msclData[0]:
        if debug:
            print('Section column found in column {0}.'.format(msclData[0].index('SECT NUM')+1))
        sectionColumn = msclData[0].index('SECT NUM')
    elif 'Section' in msclData[0]:
        if debug:
            print('Section column found in column {0}.'.format(msclData[0].index('Section')+1))
        sectionColumn = msclData[0].index('Section')
    else:
        print('ERROR: Cannot find section column. Please change section number column name to \'SECT NUM\' or \'Section\'.\n')
        exit(-1)

    # handle failure better
    if 'Section Depth' in msclData[0]:
        if debug:
            print('Section depth found in column {0}.\n'.format(msclData[0].index('Section Depth')+1))
        sectionDepth = msclData[0].index('Section Depth')
    elif 'SECT DEPTH' in msclData[0]:
        if debug:
            print('Section depth found in column {0}.\n'.format(msclData[0].index('SECT DEPTH')+1))
        sectionDepth = msclData[0].index('SECT DEPTH')
    else:
        print('ERROR: Cannot find section depth column. Please change section number column name to \'SECT DEPTH\' or \'Section Depth\'.\n')
        exit(-1)

    try:
        with open(coreList, 'r') as sectionListFile:
            fileReader = csv.reader(sectionListFile)
            for row in fileReader:
                if '\ufeff' in row[0]:
                    row[0] = row[0].replace('\ufeff','')
                    if debug:
                        print('BOM found and removed.')
                sectionList.append([int(row[0]),row[1]])
    except OSError as err:
        print("OS error: {0}".format(err))

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
        matchedData.append(row)
        unmatchedData.append(row)

    # Build the export lists, replacing the section# with the name and removing
    # the extra part_section column if the row was matched
    for row in msclData[startRow:]:
        # Does the part_section key exist in the dict?
        if row[-1] in sectionDict.keys():
            row[sectionColumn] = sectionDict[row[-1]]
            del row[-1]
            matchedData.append(row)
        else:
            unmatchedData.append(row)

    # Create a set to check unique cores names
    namedSet = set()

    # Export matched data
    with open(matchedFileName, 'w') as saveFile:
        # del matchedData[0][-1] # Delete the Part_Section column header
        filewriter = csv.writer(saveFile, delimiter=',')
        for row in matchedData:
            namedSet.add(row[sectionColumn])

            filewriter.writerow(row)

    # Cleanup
    namedSet.remove('')
    namedSet.remove(msclData[0][sectionColumn])

    coreNameList = list(sectionDict.values())
    for cn in list(set(coreNameList)):
        cnc = coreNameList.count(cn)
        if cnc > 1:
            print('WARNING: Core ' + cn + ' appears in ' + coreList + ' ' + str(cnc) + ' times.')


    # Export unmatched data
    if len(unmatchedData) > startRow:
        with open(unmatchedFileName, 'w') as saveFile:
            filewriter = csv.writer(saveFile, delimiter=',')
            for row in unmatchedData:
                filewriter.writerow(row)

    stop = timeit.default_timer()

    countDiff = len(set(sectionDict.values())) - len(namedSet)
    if (countDiff > 0):
        err = 'WARNING: Not all cores in ' + coreList + ' were used. '
        err = err + 'The following ' + str(countDiff) + ' core ' + ('names were' if countDiff != 1 else 'name was') + ' not used:'
        print(err)
        for v in list(set(sectionDict.values())):
            if (v not in namedSet):
                print(v)

    print('Completed in',round((stop - start),2),'seconds.')
    print(len(matchedData)-startRow,'rows had section names assigned (' + matchedFileName + ').')
    print('There were no unmatched rows.' if len(unmatchedData) == startRow else 'There were ' + str(len(unmatchedData)-2) + ' unmatched rows (' + unmatchedFileName + ').')


if __name__ == '__main__':
    if len(sys.argv) > 3:
        print('Usage: python renamer.py <unnamed MSCL file.csv> (<core list.csv>)')
        exit(-1)
    
    # Find the core list
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
