import sqlite3
import numpy as np
from typing import Callable
from tqdm import tqdm
import bottleneck as bn
import os
import time
import math
from matplotlib import pyplot as plt

#Roadmap:
#xmulti column update
#xmulti function analysis
#xselect pixel range
#xplot pixel range
#xgrab pixel data
#xgrab pixel data over time
#xsave plots without show()
#xanalyze multiple files
#xanalyze folder
#speed up multiscan by consolidating into one file?
# - speed benchmark pixel selection
#fft
#change over to ? from string formatting

###############################################################
#### Basic DB manipulation ###################################
###############################################################

# TODO: create cursors within functions rather than pass around a global cursor?
# Open a connection to the database specified in filepath and initialize a cursor
# Returns the database connection object and the initialized cursor
def openDB(fileName):

    connection = sqlite3.connect(fileName)

    # Set rows to be represented by sqlite3 row class
    # connection.row_factory = sqlite3.Row

    cursor = connection.cursor()

    return connection, cursor

# Inputs a cursor and a name for a table
# Outputs a list of strings with the name of every column
# Use to extract a list of parameters for a given experiment, or to check what axes were scanned along
def columnNames(cursor, table : str):

    # Generate PRAGMA table_info query
    query = "PRAGMA table_info(" + table + ")"

    res = cursor.execute(query).fetchall()

    # The result will be a list of tuples. The name of the column is entry 1
    names = []
    for column in res:
        names.append(column[1])

    return names

# Inputs a cursor and table name
# Outputs the number of rows in the table
def numberOfRows(cursor, table: str):

    query = "SELECT COUNT(*) FROM " + table

    res = cursor.execute(query)

    return res.fetchone()[0]


# Retrieve experiment parameters
# Takes a cursor object and a name of the table containing the parameters (default 'parameters')
# Outputs a dict with the column names as keys and the first row as values
def retrieveParameters(cursor, table = 'parameters'):

    # Retrieve column names to use as keys
    paramNames = columnNames(cursor, table)

    # Combine the keys into a SELECT query
    query = 'SELECT ' + ", ".join(paramNames) + ' FROM ' + table

    # Fetch the first (and only) row
    res = cursor.execute(query)
    paramValues = res.fetchone()

    # Contruct a dict with the keys and the query result
    paramDict = dict(zip(paramNames, paramValues))

    return paramDict

# A function that executes an UPDATE query at a single (row,col) in the DB but does not commit it
#   Avoiding commits gives a large speed improvement when iterating over many rows
# Inputs the cursor objects, the name of the column to update, the name of the table
#     and the column and value to use as the row identifier (should be the PRIMARY KEY of the table)
# Outputs nothing
def updateCol(cur, column : str, table : str, value, keyCol, keyVal):

    # Generate the UPDATE query
    updateQuery = "UPDATE " + table + " SET " + column + " = " + str(value) + " WHERE " + keyCol + " = " + str(keyVal)

    # Execute and commit the result
    cur.execute(updateQuery)

# Adds multiple values to multiple columns within a row. Executes the UPDATE query but does not commit
# Inputs cursor, a list of columns, a table name, a list of values, and a key columns and value to identify the row (should use PRIMARY KEY as the keyCol)
def updateCols(cur, columns : list, table : str, values : list, keyCol : str, keyVal):

    # convert the columns and values lists into properly formatted strings
    formattedColumns = "(" +  ", ".join(columns) + ")"
    formattedValues = str(tuple(values))

    # Generate UPDATE query, execute
    updateQuery = "UPDATE " + table + " SET " + formattedColumns + " = " + formattedValues + " WHERE " + keyCol + " = " + str(keyVal)
    cur.execute(updateQuery)


# Create a new column within a table
def createNewColumn(con, cur, table : str, columnName : str):

    # Create query from input
    query = "ALTER TABLE " + table + " ADD COLUMN " + columnName + " REAL"

    try:
        cur.execute(query)
        con.commit()
    except sqlite3.OperationalError:
        print("Error creating new column. Column likely already exists. Data will be overwritten")

# delete an existing column in a table. USE WITH CAUTION
def deleteColumn(con, cur, table: str, columnName: str):

    # Create query from input
    query = "ALTER TABLE " + table + " DROP COLUMN " + columnName

    cur.execute(query)
    con.commit()


# Function to lookup data from dataColumns list using collection_index as the selection parameter
#   Using collection_index is much faster than other search criteria
def fastLookup(cursor, index: int, dataColumns: list, table='acoustics'):

    # generate a where query using the pixel's index
    whereCondition = "collection_index = " + str(index)

    # format the datacolumns for the query
    formattedDataColumns = ", ".join(dataColumns)

    # Combine info into a SELECT query
    selectQuery = "SELECT " + formattedDataColumns + " FROM " + table + " WHERE " + whereCondition

    # Execute query and fetch data
    cursor.execute(selectQuery)
    # fetchone() is used because we are searching by primary key so only one result should return
    data = cursor.fetchone()

    return data

##########################################################################
########## Data Analysis #################################################
#########################################################################

# Applies a function to a data set by iterating through it line by line and stores the result
# Inputs: database cursor, the function to apply to the dataset, the name of the column to store the result in
#   the column names to retrieve the data from (a list of strings), and the name of the table to retrieve from
# NOTE: func is assumed to operate on a list of two arrays i.e. [ ([x1,x2,...]), ([y1,y2,...])]
# Outputs: the result of applying the function to all rows as a list. It also writes the result into a new column in the database
# TODO: this function has become bloated and might need to be broken up
def applyFunctionToData(connection, cursor, func : Callable, resName : str, dataColumns = ['time', 'voltage'], keyColumn = ['collection_index'], table = 'acoustics', *funcArgs):

    # Gather the number of rows in the db
    numRows = numberOfRows(cursor, table)

    # Create a new column in the table to hold the generated data
    createNewColumn(connection, cursor, table, resName)

    # Generate and execute a db query to get the data and the primary key
    columnsToSelect = dataColumns + keyColumn
    selectQuery = "SELECT " + ", ".join(columnsToSelect) + " FROM " + table

    res = cursor.execute(selectQuery)

    writeCursor = connection.cursor()

    funcResultList = []

    # Iterate through the result, convert the data to numpy arrays, apply the function, and save the result
    for i in tqdm(range(numRows)):

        row = res.fetchone()

        # Initialize a list to save the data arrays
        arrayList = []

        # row is a tuple of length >= 2, with the final entry being the primary key
        # convert each entry in row to an array except the final primary key
        for i in range(len(row) - 1):
            arrayList.append(stringListToArray(row[i]))

        # Retrieve the primary key value of the row as the last member
        keyValue = row[-1]

        funcResult = func(arrayList, *funcArgs)

        updateCol(writeCursor, resName, table, funcResult, keyColumn[0], keyValue)

        funcResultList.append(funcResult)

    connection.commit()

    return funcResultList

# Version of applyFunctionToData that applies muliple functions to the same data set and saves it
#   This version should be significantly faster vs calling applyFunctionToData multiple times
#   because it minimizes the number of read/write steps
# funcs is now a list of callable functions
# Inputs: connection and cursor objects, a list of functions to apply, a list of column names for the results (index matched to funcs),
#   a list of 2 data columns to apply the functions to (i.e. times vs voltage), the key column (the PRIMARY KEY) used to identify the rows,
#   a table name, and an option funcArgs dict which maps the functions to a tuple of additional arguments (e.g. for staltaFirstBreak)
# Outputs nothing, but writes results to the database
def applyFunctionsToData(connection, cursor, funcs : list, resNames : list, dataColumns = ['time', 'voltage'], keyColumn = ['collection_index'], table = 'acoustics', funcArgs = {}):

    # Gather the number of rows in the db
    numRows = numberOfRows(cursor, table)

    # Create a new column in the table for each function to be calculated
    for col in resNames:
        createNewColumn(connection, cursor, table, col)

    # Generate and execute a db query to get the data and the primary key
    columnsToSelect = dataColumns + keyColumn
    selectQuery = "SELECT " + ", ".join(columnsToSelect) + " FROM " + table

    res = cursor.execute(selectQuery)

    writeCursor = connection.cursor()

    # Iterate through the result, convert the data to numpy arrays, apply the functions, and save the results
    for i in tqdm(range(numRows)):

        row = res.fetchone()

        # Initialize a list to save the data arrays
        arrayList = []

        # row is a tuple of length >= 2, with the final entry being the primary key
        # convert each entry in row to an array except the final primary key
        for i in range(len(row) - 1):
            arrayList.append(stringListToArray(row[i]))

        # Retrieve the primary key value of the row as the last member
        keyValue = row[-1]

        funcResults = []

        extraArgs = ()

        for func in funcs:

            # Run func with extra arguments if func is in the funcArgs dict
            if func in funcArgs:
                funcResults.append(func(arrayList, *funcArgs[func]))

            else:
                funcResults.append(func(arrayList))

        # write func results into current row
        updateCols(writeCursor, resNames, table, funcResults, keyColumn[0], keyValue)

    connection.commit()

# Function that runs applyFunctionsToData on multiple databases
# Setting verbose = True will print the name of each file as it is analyzed
def analyzeDatabases(fileNames : list, funcs : list, resNames : list, dataColumns = ['time', 'voltage'], keyColumn = ['collection_index'], table = 'acoustics', funcArgs = {}, verbose = True):

    #Iterate through filenames
    for file in fileNames:

        if verbose == True:
            print("Analyzing " + file)

        #Create DB connection
        con, cur = openDB(file)

        #Run applyFunctionsToData
        applyFunctionsToData(con, cur, funcs, resNames, dataColumns, keyColumn, table, funcArgs)

        #Close connection
        con.close()

def analyzeDirectory(dir, funcs : list, resNames : list, dataColumns = ['time', 'voltage'], keyColumn = ['collection_index'], table = 'acoustics', funcArgs = {}, verbose = True):

    # Grab list of files with .sqlite3 extension in the folder
    files = os.listdir(dir)
    fileNames = []
    for file in files:
        if file.endswith(".sqlite3"):
            fileNames.append(os.path.join(dir, file))

    # Analyze gathered files
    analyzeDatabases(fileNames, funcs, resNames , dataColumns, keyColumn, table, funcArgs, verbose)

# Perform a routine set of analysis of multiscan data within a folder
# Analysis functions: absolute_sum, arrayMax, and staltaFirstBreak(5,30,0.75)
# Results are stored as columns with the function names and parameters
def defaultMultiScanAnalysis(dir):

    # list functions and dict their optional parameters
    funcList = [absoluteSum, arrayMax, staltaFirstBreak]
    funcParams = {staltaFirstBreak : (5, 30, 0.75)}

    # Convert function and parameter information into column names
    # Functions with parameters are stored as functionName_(parameters)
    colNames = []
    for func in funcList:
        if func in funcParams:
            # funcParams must be converted from tuple to underscored list to avoid confusing later SQL calls with parenthesis
            # also replaces decimal points with 'd'
            formattedParams = str(funcParams[func]).strip('()').replace(', ', '_').replace('.', 'd')
            colNames.append(str(func.__name__) + '_' + formattedParams)
        else:
            colNames.append(str(func.__name__))

    # run analysis
    analyzeDirectory(dir, funcList, colNames, funcArgs = funcParams)

    # generate plots
    generate2DScansDirectory(dir, 'X', 'Z', colNames)

# Retrieves the values in dataColumn at a given pixel coordinate
def singleDataAtPixel(cursor, dataColumn : str, primaryCoor, secondaryCoor, primaryAxis = 'X',  secondaryAxis = 'Z', table = 'acoustics'):

    # start = time.time()
    # format axes and coors into a WHERE statement
    whereCondition = primaryAxis + " = " + str(primaryCoor) + " AND " + secondaryAxis + " = " + str(secondaryCoor)

    # Combine info into a SELECT query
    selectQuery = "SELECT " + dataColumn + " FROM " + table + " WHERE " + whereCondition

    # Execute query and fetch data
    cursor.execute(selectQuery)
    data = cursor.fetchone()
    # queryTime = time.time() - start

    # If data was not found, print a warning and return None
    # Otherwise, convert the data to floats and put it with the correct data key
    if data == None:
        print("dataAtPixel: no data returned. Check that the provided coordinates (" + str(primaryCoor) + ", " + str(secondaryCoor) + ") exist within the data set")
        return None
    else:
        return float(data[0])

#TODO: combine select calls into single query w/ OR, then fetchall
#   even faster: convert coors to collection_index - need to quickly calculate coor steps
def dataAtPixels(cursor, dataColumns : list, primaryCoors : list, secondaryCoors : list, primaryAxis = 'X',  secondaryAxis = 'Z', table = 'acoustics'):

    # check that primary and secondary coor lists are valid
    if len(primaryCoors) != len(secondaryCoors):
        print("dataAtPixels: length of primaryCoors and secondaryCoors must be equal. Returning None")
        return None

    # generate (x,y) tuples from primary and secondary coors
    coorList = []
    for i in range(len(primaryCoors)):
        coorList.append((primaryCoors[i], secondaryCoors[i]))

    dataDict = {}
    # iterate through coordinates and run dataAtPixel for each one
    for coor in coorList:
        start = time.time()
        dataDict[coor] = dataAtPixel(cursor, dataColumns, coor[0], coor[1], primaryAxis, secondaryAxis, table)
        stop = time.time()
        print('data collection time = ' + str(stop - start))

    return dataDict

# Retrieves the values in dataColumns at a given pixel coordinate
# Returns the values as an dict with dataColumns as the keys and the float-converted data as values
# Explanation for the speedup can be found in the function coordinatesToCollectionIndex
def fastDataAtPixel(cursor, dataColumns : list, primaryCoor, secondaryCoor, primaryAxis = 'X',  secondaryAxis = 'Z', table = 'acoustics', verbose = False):

    # Convert input coordinate to a collection_index
    pixelIndex = coordinatesToCollectionIndex(cursor, [primaryCoor], [secondaryCoor], primaryAxis, secondaryAxis, table, verbose)[0]

    data = fastLookup(cursor, pixelIndex, dataColumns, table)

    dataDict = {}
    # If data was not found, print a warning and return None
    # Otherwise, convert the data to floats and put it with the correct data key
    if data == None:
        print("dataAtPixel: no data returned. Check that the provided coordinates (" + str(primaryCoor) + ", " + str(
            secondaryCoor) + ") exist within the data set")
        return None
    else:
        for i in range(len(data)):
            dataDict[dataColumns[i]] = float(data[i])
        return dataDict

# Retrieves the values in dataColumns for given pixel coordinates
# Returns the values as a dict of dicts with dataColumns as the keys and the float-converted data as values
#                 (x0, z0) : {column 0 : val 00, column 1 : val 01, ...}
#   pixelsDat = { (x1, z1) : {column 0 : val 10, column 1 : val 11, ...}  }
#                 (x2, z2) : {column 0 : val 20, column 1 : val 21, ...}
# Explanation for the speedup can be found in the function coordinatesToCollectionIndex
def fastDataAtPixels(cursor, dataColumns: list, primaryCoors, secondaryCoors, primaryAxis='X', secondaryAxis='Z', table='acoustics', verbose=False):

    # check that primary and secondary coor lists are valid
    if len(primaryCoors) != len(secondaryCoors):
        print("dataAtPixels: length of primaryCoors and secondaryCoors must be equal. Returning None")
        return None

    # Convert input coordinate to a collection_index
    pixelIndices = coordinatesToCollectionIndex(cursor, primaryCoors, secondaryCoors, primaryAxis, secondaryAxis, table, verbose)

    coorDict = {}
    # iterate through pixels, grab data, convert to a dict, add to coorDict
    for i in range(len(pixelIndices)):
        index = pixelIndices[i]
        coor = (primaryCoors[i], secondaryCoors[i])
        dataDict = {}
        if index == None:
            print(
                "fastDataAtPixels: data index is None. Check that the provided coordinates (" + str(coor[0]) + ", " + str(
                    coor[1]) + ") exist within the data set")
            for i in range(len(dataColumns)):
                dataDict[dataColumns[i]] = None
        else:
            data = fastLookup(cursor, index, dataColumns, table)
            for i in range(len(dataColumns)):
                dataDict[dataColumns[i]] = float(data[i])
        coorDict[coor] = dataDict.copy()

    return coorDict

# Function to convert coordinates to a collection_index
    # Inputs a list of coordinates and axes, outputs the collection_index corresponding to each coordinate
# This does some algebra to massively speed up queries. More details are here:
#       Motivation: SQL searches are O(1) or O(ln n) with the int primary key (vs O(n) w/ other keys)
#       In order to search for pixels by primary key, we need a function which converts a given coordinate to a collection_index
#           This requires some algebra since we do not know a priori what the coordinate steps are. We must solve that using
#           the known ranges and a few sample coordinates. The math works as follows:
#           For an (x,z) scan, let xs, zs be the coordinate step that the map was collected at
#           Let (xf, zf) be the final coordinates at the last collection_index kf
#           Let (x0, z0) be the coordinates of the second to last collection_index k0 = kf - 1
#                Looking up both of these coordinates takes O(1) time since we start from collection_index
#           Let (m, n) be the number of rows and columns of a given map
#           Our system of equations is then:
#               1)  kf = nm - 1
#               2)  xf = (n - 1) xs
#               3)  zf = (m - 1) zs
#               4)  kf = n (zf / zs) + xf/xs
#               5)  k0 = n (z0 / zs) + x0/xs
#               6) either xs = xf - x0 OR zs = zf - z0
#           We can directly solve (6) by checking which coordinate changes between kf and k0
#           The other unknowns (n, m, the remaining of xs or zs) can then be solved straighforwardly
def coordinatesToCollectionIndex(cursor, primaryCoors : list, secondaryCoors : list, primaryAxis = 'X',  secondaryAxis = 'Z', table = 'acoustics', verbose = True):

    # check that primary and secondary coor lists are valid
    if len(primaryCoors) != len(secondaryCoors):
        print("dataAtPixels: length of primaryCoors and secondaryCoors must be equal. Returning None")
        return None

    # Collect the needed constants
    # We will be using x as the primary coordinate and z as the secondary to match most common scanning data
    # (kf, xf, zf)
    kf = numberOfRows(cursor, table) - 1
    # Do some quick error checking - make sure kf > 0 or else the rest will fail
    if kf <= 1:
        print("coordinatesToCollectionIndex: input table only has one row. Check that the table and data are correct")
        return None
    # xf, zf == coordinates at kf
    formattedCoordinates = primaryAxis + ", " + secondaryAxis
    xfzfQuery = "SELECT " + formattedCoordinates + " FROM " + table + " WHERE collection_index = " + str(kf)
    xfzfTuple = cursor.execute(xfzfQuery).fetchone()
    xf = xfzfTuple[0]
    zf = xfzfTuple[1]

    # collect a second set of (k, x, z) at the second to last coordinate
    k0 = kf - 1
    x0z0Query = "SELECT " + formattedCoordinates + " FROM " + table + " WHERE collection_index = " + str(k0)
    x0z0Tuple = cursor.execute(x0z0Query).fetchone()
    x0 = x0z0Tuple[0]
    z0 = x0z0Tuple[1]

    # Check which coordinate changed and use that to solve the equations
    # First handle case where x coordinate changed
    if zf == z0:
        xs = xf - x0
        n = (xf / xs) + 1
        m = (kf + 1) / n
        zs = zf / (m - 1)
    elif xf == x0:
        zs = zf - z0
        m = (zf / zs) + 1
        n = (kf + 1) / m
        xs = xf / (n - 1)
    # We should not enter the final branch, but just in case lets put a panicked error message
    else:
        print("coordinatesToCollectionIndex: unable to identify coordinate step. Unclear what went wrong, but its probably related to floating point rounding. Your data is probably cursed, contact Sam for an exorcism (or debugging).")
        return None

    # Now iterate through the input coordinates and convert to indices
    # using equation k = n(z/zs) + (x/xs)
    collectionIndices = []

    for i in range(len(primaryCoors)):
        x = primaryCoors[i]
        # Raise warnings if rounding
        if verbose == True and (x % xs != 0):
            print('coordinatesToCollectionIndex: primary coordinate ' + str(x) + 'is not a multiple of the primary step. Rounding coordinate.')

        z = secondaryCoors[i]
        if verbose == True and (z % zs != 0):
            print('coordinatesToCollectionIndex: secondary coordinate ' + str(z) + 'is not a multiple of the secondary step. Rounding coordinate.')

        index = (n * (z / zs)) + (x / xs)

        # handle out of bounds indices as None
        if index <= 0:
            collectionIndices.append(None)
        else:
            collectionIndices.append(int(index))

    return collectionIndices

# Retrieves the values in dataColumns at a given pixel coordinate
# Returns the values as an dict with dataColumns as the keys and the float-converted data as values
def dataAtPixel(cursor, dataColumns : list, primaryCoor, secondaryCoor, primaryAxis = 'X',  secondaryAxis = 'Z', table = 'acoustics'):

    # use collection_index to make a WHERE statement
    whereCondition = primaryAxis + " = " + str(primaryCoor) + " AND " + secondaryAxis + " = " + str(secondaryCoor)

    # Format data columns
    formattedDataColumns = ", ".join(dataColumns)

    # Combine info into a SELECT query
    selectQuery = "SELECT " + formattedDataColumns + " FROM " + table + " WHERE " + whereCondition

    # Execute query and fetch data
    cursor.execute(selectQuery)
    data = cursor.fetchone()

    dataDict = {}
    # If data was not found, print a warning and return None
    # Otherwise, convert the data to floats and put it with the correct data key
    if data == None:
        print("dataAtPixel: no data returned. Check that the provided coordinates (" + str(primaryCoor) + ", " + str(secondaryCoor) + ") exist within the data set")
        return None
    else:
        for i in range(len(data)):
            dataDict[dataColumns[i]] = float(data[i])
        return dataDict

# TODO: this is very slow (~500 ms / iteration). find the bottleneck and speed it up
# Runs dataAtPixels across multiple scans,
# Returns a dict with the keys as (x,y) coordinates, and the values as a dict with keys as data columns and values as a numpy array
def multiScanDataAtPixels(fileNames : list, dataColumns : list, primaryCoors : list, secondaryCoors : list, primaryAxis = 'X',  secondaryAxis = 'Z', table = 'acoustics', verbose = True):

    # initialize storage list
    dataDictList = []

    # Iterate through files
    for file in fileNames:

        if verbose == True:
            print("Gathering data from " + file)

        # open connection
        con, cur = openDB(file)

        # collect data at pixels
        dataDictList.append(fastDataAtPixels(cur, dataColumns, primaryCoors, secondaryCoors, primaryAxis, secondaryAxis, table))

        con.close()

    # Merge data. storage list is a list of dicts of dicts. This got ugly...

    # First make a copy of dataDictList[0] but with the values as numpy arrays
    masterDict = {}

    for coordinate, coordinateData in dataDictList[0].items():
        masterDict[coordinate] = {dataColumn : np.array(value) for dataColumn, value in coordinateData.items()}

    # Now iterate through the rest of dataDictList, merging the values into the arrays of masterDict
    for scan in dataDictList[1:]:

        # for each scan in list, iterate through the keys (coordinates) and values (values == innerDict of data columns)
        for key, coordinateData in scan.items():

            # set the value of masterDict[coordinate/key][data column / inn
            for dataColumn, value in coordinateData.items():
                masterDict[key][dataColumn] = np.append(masterDict[key][dataColumn], value)

    return masterDict

# Runs multiScanDataAtPixels on all of the files within a given directory
# Returns a dict with the keys as (x,y) coordinates, and the values as a dict with keys as data columns and values as a numpy array
def directoryScanDataAtPixels(dir : str, dataColumns : list, primaryCoors : list, secondaryCoors : list, primaryAxis = 'X',  secondaryAxis = 'Z', table = 'acoustics', verbose = True):

    # Grab list of files with .sqlite3 extension in the folder
    files = os.listdir(dir)
    fileNames = []
    for file in files:
        if file.endswith(".sqlite3"):
            fileNames.append(os.path.join(dir, file))

    data = multiScanDataAtPixels(fileNames, dataColumns, primaryCoors, secondaryCoors, primaryAxis, secondaryAxis, table, verbose)

    return data

# Helper function to convert a 'stringified' list ('[1.1, 3.2, 4.3]') into a numpy array ([1.1, 3.2, 4.3])
# Inputs the string, outputs the list
# Used to convert sql-saved lists into numpy arrays
# TODO: in the future, saving and loading can be made smarter - save the data as binary and directly load it into an array
def stringListToArray(strList : str):

    # Reformat the string by removing brackets and splitting along the ','
    strFormatted = strList.strip('[]').split(', ')

    floatList = []
    # Convert the string numbers to floats
    for num in strFormatted:
        floatList.append(float(num))

    return np.array(floatList)

########################################################################
################## Plotting ############################################
########################################################################

# plot the first waveform in the db
def plotWaveform(cursor, xCol = 'time', yCol = 'voltage', table = 'acoustics'):

    # Format the requested columns for the db query
    columns = xCol + ', ' + yCol

    # Formate and execute SELECt query
    selectQuery = "SELECT " + columns + " FROM " + table

    rawData = cursor.execute(selectQuery).fetchone()

    xDat = stringListToArray(rawData[0])
    yDat = stringListToArray(rawData[1])

    plt.plot(xDat, yDat)
    plt.show()

# TODO: finish this now that dataAtPixel is done
# def plotPixel(cursor, primaryCoor, secondaryCoor, primaryAxis = 'X', secondaryAxis = 'Z', xCol = 'time', yCol = 'voltage', table = 'acoustics'):
#
#     dataColumns = xCol + ', ' + yCol
#
#     # Format pixel coordinates as a WHERE statement
#     wherePixel = 'WHERE ' +

# Generates a plot of the given data column at certain coordinate values for all databases in a directory
# Plot x-axis is the first entry in dataColumns, y-axis is the second
# useful for multiscans
#TODO: add conversion if x-axis is time
def plotScanDataAtPixels(dir : str, dataColumns : list, primaryCoors : list, secondaryCoors : list, primaryAxis = 'X',  secondaryAxis = 'Z', table = 'acoustics', verbose = True):

    dataDict = directoryScanDataAtPixels(dir, dataColumns, primaryCoors, secondaryCoors, primaryAxis, secondaryAxis, table, verbose)

    for coor in dataDict.keys():
        plt.scatter(dataDict[coor][dataColumns[0]], dataDict[coor][dataColumns[1]], label = str(coor))

    plt.legend()
    # plt.show()


# plot a map
def plot2DScan(cursor, xCol : str, yCol : str, datCol : str, save = False, show = True, fileName = '', table = 'acoustics'):

    # Format the requested columns for the db query
    columns = xCol + ', ' + yCol + ', ' + datCol

    # Formate and execute SELECt query
    selectQuery = "SELECT " + columns + " FROM " + table

    rawData = cursor.execute(selectQuery).fetchall()

    xDat = np.array([])
    yDat = np.array([])
    cDat = np.array([])

    for row in rawData:
        xDat = np.append(xDat, float(row[0]))
        yDat = np.append(yDat, float(row[1]))
        cDat = np.append(cDat, float(row[2]))

    plt.scatter(xDat, yDat, c = cDat)
    plt.colorbar()

    if save == True:
        plt.savefig(fileName)
        plt.close()

    if show == True:
        plt.show()

    # Make SELECT query

    # Convert data to np arrays

    # plot

# Function to generate plots from several DB files.
# Saves plots from multiple files and can handle multiple data columns to plot as the z (color) axis
# Save the plots as datCol//fileName_datCol
def generate2DScans(fileNames : list, xCol : str, yCol : str, datCols : list, format = '.png', verbose = True):

    for file in fileNames:

        if verbose == True:
            print("Plotting " + file)

        # Open database connection
        con, cur = openDB(file)

        for dat in datCols:

            # Generate the save filename for each plot
            # Puts each different type of data plot in a separate folder for easier organization
            saveDir = os.path.dirname(file) + '//' + dat + '//'

            # make the saveDir if it doesn't exist
            if not os.path.exists(saveDir):
                os.makedirs(saveDir)

            # Generate savename by gathering the basename, removing the exension, adding the data column name and format extension
            saveName = os.path.basename(os.path.splitext(file)[0]) + dat + format
            saveFile = saveDir + saveName

            # run plot2dscan with save = True and show = False
            plot2DScan(cur, xCol, yCol, dat, save = True, show = False, fileName = saveFile)

        # Close db connection
        con.close()

def generate2DScansDirectory(dir, xCol : str, yCol : str, datCols : list, format = '.png', verbose = True):

    # Grab list of files with .sqlite3 extension in the folder
    files = os.listdir(dir)
    fileNames = []
    for file in files:
        if file.endswith(".sqlite3"):
            fileNames.append(os.path.join(dir, file))

    # run multiGenerateScanPlots with the list of fileNames
    generate2DScans(fileNames, xCol, yCol, datCols, format, verbose)

##########################################################################33
############### Analysis Functions #########################################
##### For use with applyFunctionToData ###################################
###########################################################################

# Simple function to take the sum of the absolute values of the 'y' values
def absoluteSum(arrList):
    return bn.nansum(abs(arrList[1]))

# Return the  max of the y-values
def arrayMax(arrList):
    return bn.nanmax(arrList[1])

# Calculate the time of the first break using STA/LTA algorithm
# Inputs the arrayList from applyFunctionToData, the length (in number of elements, NOT time) of the short and long averaging window,
#   and tresholdRatio, a number in (0,1) that determines what fraction of the maximum STA/LTA counts as the first break
def staltaFirstBreak(arrayList, shortWindow : int, longWindow : int, thresholdRatio = 0.75):

    # Assume that arrayList is (time, voltage) data
    timeData = arrayList[0]
    voltageData = arrayList[1]

    staltaArray = stalta(voltageData, shortWindow, longWindow)

    threshold = thresholdRatio * bn.nanmax(staltaArray)

    # Return time where first value in staltaArray is above threshold
    for i in range(len(staltaArray)):
        if staltaArray[i] > threshold:
            return timeData[i]

    # No value was found above threshold. Return -1
    return -1

###########################################################################
########## Analysis Helper Functions ####################################
#### Do not directly use with applyFunctionToData ###########################
########################################################################

# Calculate STA/LTA for a given short and long window
# Windows are specified in number of elements (not time)
# Returns an array of the same length as input. Values within longWindow-1 of the start of the array will be converted to NaNs
# NOTE: windows are left-handed in this implementation
def stalta(array, shortWindow, longWindow):
    # Calculate square of array values
    arrSquared = array ** 2

    # Calculate moving averages with optimized code from bottleneck package
    sta = bn.move_mean(arrSquared, shortWindow)
    lta = bn.move_mean(arrSquared, longWindow)

    return sta / lta