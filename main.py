import pandas as pd
import time
from colorama import Fore, Back, Style
from pathlib import Path

#LIMITATIONS:
# - cannot handle gaps in data table. 

#FUNCTIONS
#pass the dataFrame you would like to export. Will ask user to confirm and input their path and file name. 
#returns 0 if negitive confirmation and 1 if exported
def export(data):
    check = input('Would you like to export your data as it is? Y/N')
    if check != 'Y' and check != 'y':
        return(0)
    else:
        path = Path(input('Please enter the path and file name you would like: \n'))
        path.parent.mkdir(parents=True, exist_ok=True)
        data.to_csv(path)
        return(1)
    

#BODY

# Ask for user imput to get path to file and import file into data frame
# also raise exception if data is not .xlsx or .csv file type
path = input('Ender the path to the file you would like to analize:\n')
if(path[-5:] == '.xlsx'):
    dataImported = pd.read_excel(path)
elif(path[-4:] == '.csv'):
    dataImported = pd.read_csv(path)
else:
    raise(ImportError(Fore.RED + "file type not supported. Please double check you typed the path correctly." + Style.RESET_ALL))



# find the first and last row that contains data. 
# Var is yBounds = [top of data, bottom of data]
# xBounds remains constant for all sheet assumeing they were not messed with
xBounds = [2,14]
yBounds = []
# top bound
try:
    for row in range(0,500):
        if (dataImported.loc[row, 'Unnamed: 2'] == 1 and
            dataImported.loc[row, 'Unnamed: 3'] == 2 and
            dataImported.loc[row, 'Unnamed: 4'] == 3):
            yBounds.append(row)
            break
except:
    exit (Fore.RED + 'No top bound was found.' + Style.RESET_ALL)
    
# bottom bound
try:
    for row in range(yBounds[0],500):
        if (str(dataImported.loc[row, 'Unnamed: 2']) == 'nan'):
            yBounds.append(row)
            break
except:
    yBounds.append(row)

# xBounds and yBounds to capture imported data and att them to a new dataFrame called dataScrubbed
dataScrubbed = dataImported.loc[range(yBounds[0],yBounds[-1]), ['Unnamed: ' + str(x) for x in range(xBounds[0],xBounds[-1])]]
#make the top column into column titles
dataScrubbed.columns = [int(i) for i in dataScrubbed.iloc[0]]
dataScrubbed = dataScrubbed.tail(-1)

# make indexs for each plate row letter A-H and numbered per read. For example row A read 3 would be 'A3'
index = []
for i in range(1, len(dataScrubbed) + 1):
    if (i <= 1*len(dataScrubbed)/8):
        index.append('A' + str(int(i)))
    elif (i <= 2*len(dataScrubbed)/8):
        index.append('B' + str(int(i - 1*len(dataScrubbed)/8)))
    elif (i <= 3*len(dataScrubbed)/8):
        index.append('C' + str(int(i - 2*len(dataScrubbed)/8)))    
    elif (i <= 4*len(dataScrubbed)/8):
        index.append('D' + str(int(i - 3*len(dataScrubbed)/8)))
    elif (i <= 5*len(dataScrubbed)/8):
        index.append('E' + str(int(i - 4*len(dataScrubbed)/8)))
    elif (i <= 6*len(dataScrubbed)/8):
        index.append('F' + str(int(i - 5*len(dataScrubbed)/8)))
    elif (i <= 7*len(dataScrubbed)/8):
        index.append('G' + str(int(i - 6*len(dataScrubbed)/8))) 
    elif (i <= 8*len(dataScrubbed)/8):
        index.append('H' + str(int(i - 7*len(dataScrubbed)/8))) 

# apply created indexs to scrubbed data
dataScrubbed.index = index


# Check with user to ensure data was found and scrubbed properly
print (Back.LIGHTBLACK_EX + 'DATA DETECTED:' + Style.RESET_ALL)
print(dataScrubbed)

dataCheckResponse = input('please enter "Y" to varify that the above data is the data you would like processed:\n' )
if dataCheckResponse != 'Y' and dataCheckResponse != 'y':
    exit(Fore.RED + 'Failed to properly read data. Please remove any information in your file above the data section and try again. \nDo not change the data section in any way.' + Style.RESET_ALL)
print (Fore.GREEN + 'You verified that the above is your data.', Style.RESET_ALL)

# wait to increase readability and ask if user wants to continue
time.sleep(0.25)
correctionsResponse = input('\nWould you like to correct your data using one or more correction reads? Y/N:\n')

# if they don't want to coninue run export()
if (correctionsResponse == 'N' or correctionsResponse == 'n'):
    export(dataScrubbed)
    exit()


# correct data by subtracting every odd line by the even line below. OVERFLOW data will be replaced by None values
dataCorrected = pd.DataFrame(columns=range(1,13))
for row in dataScrubbed.index:
    if (int(row[1:]) % 2 == 0):
        pass
    else:
        for column in dataScrubbed.columns:
            try:
                dataCorrected.loc[row, column] = dataScrubbed.loc[row, column] - dataScrubbed.loc[row[0] + str( int(row[1:]) + 1 ), column]
            except:
                dataCorrected.loc[row, column] = None
    
print ('Corrected data:\n', dataCorrected)

# ask for input for data selection
selectionResponse = input('Would you like to select the best data replicate? Y/N\n')
ladderColumnsResponse = input('Please enter the following information:\nyour ladder columns by column number separated by comma and space. For example "1, 2":\n')
upperResponse = input('Upper limit (greater than): ')
lowerResponse = input('Lower limit (less than): ')
percentErrorToleranceRespoonse = input('Acceptable percent % error (enter without %): ')

# if declined call export()
if selectionResponse == 'N' or selectionResponse == 'n':
    export(dataCorrected)
    exit()

# parse ladder columns input to create a list
ladderColumns = [int(i) for i in ladderColumnsResponse.split(', ')]

# calculate the percent error for ladder columns. Row index is used as key.
percentErrors = {}
for row in dataCorrected.index:
    n = len(ladderColumns)
    xi = [i for i in dataCorrected.loc[row, ladderColumns]]
    u = sum(dataCorrected.loc[row, ladderColumns])/len(ladderColumns)
    percentErrors[row] = (((sum([(i - u)**2 for i in xi]))/n)**0.5 )/u*100
    
# Make a list of max percent error values for each plate read. Read number is used as key.
errorMaxs = {}
for item in percentErrors.items():
    if item[0][1:] not in errorMaxs.keys():
        errorMaxs[item[0][1:]] = item[1]
    elif item[1] > errorMaxs[item[0][1:]]:
        errorMaxs[item[0][1:]] = item[1]
        
# sort errorMaxs dictionary by value. Lower values first.
errorMaxs = dict(sorted(errorMaxs.items(), key=lambda item:item[1]))

# Run through each plate in order of lower max percent error first, higher max percent error last.
# Test if read's ladder fits paramaters set by user and save if so
dataSelected = pd.DataFrame(columns=range(1,13))
for key in errorMaxs.keys():
    if sum(dataCorrected.loc['A' + key, ladderColumns])/len(ladderColumns) > float(upperResponse) and sum(dataCorrected.loc['H' + key, ladderColumns])/len(ladderColumns) < float(lowerResponse):
        for letter in ['A','B','C','D','E','F','G','H']:
            if any(i is None for i in [v for v in dataCorrected.loc[letter + key]]) or errorMaxs[key] > float(percentErrorToleranceRespoonse):
                dataSelected = pd.DataFrame(columns=range(1,13))
                break
            else:
                dataSelected.loc[letter + key] = dataCorrected.loc[letter + key]
                print(dataSelected)        

print(Back.LIGHTBLACK_EX + 'DATA SELECTED:' + Style.RESET_ALL)
print(dataSelected)
print(Fore.GREEN + 'Accepted maximum percent error:' + Style.RESET_ALL, errorMaxs[dataSelected.index[0][1:]])
export(dataSelected)
