#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jul 17 14:54:39 2020

@author: kewilliams (minor modifications by gdancik)

usage: python extract_data_for_html.py [-h] dataFile page inputState update-type [geckoDriverPath]

Retrieve data from covidactnow.org for overall covid threat, daily new cases, infection rates
positive test rates, icu availability, and contract tracing coverage.

Guaranteed data collection or new creation of data file.  HTML generation based on increaseOnly variable,
can either always generate or only generate when an increase in a threat level is detected.

All data gathered by xpath as selenium methods are unable to gather targeted data in this instance.

xpaths selected are not specific to state and are valid for all us state abbreviations
"""

from selenium import webdriver
from selenium.webdriver.firefox.options import Options
# import pandas as pd
import os
import time
import argparse
import sys
from datetime import date
import datetime


def getWebData (inputState, geckoPath):
    
    options = Options()
    options.headless = True
    
    if not geckoPath:
        driver = webdriver.Firefox(options = options)
    else:
        driver = webdriver.Firefox(options = options, executable_path=geckoPath)
    
    driver.get('https://www.covidactnow.org/us/' + inputState)
    
    time.sleep(1) # allow page load
    
    # get overall threat level. text \n delimited - first index ignored ('COVID THREAT LEVEL')
    threatLevelXpath = "//div[@class='MuiBox-root jss20 sc-qapaw fXKKch']"
    threatLevel = driver.find_element_by_xpath(threatLevelXpath)
    threatLevel = threatLevel.text.split('\n')[1:]
    # condense threat level string, arguably only need first sentence or up to first comma.
    threatLevel[1] = threatLevel[1].replace(',', '.').split('.')[0]
    
    # get overall risk, text /n delimited
    overallRiskXpath = "//div[@class='sc-fznLPX dtmoaU']"
    overallRisk = driver.find_element_by_xpath(overallRiskXpath).text.split('\n')
    state = overallRisk[0] # get state string
    overallRisk = overallRisk[2] # overwrite list to string containing risk
    
    # numerical values for all categories accessed by same xpath
    ctDataXpath = "//p[@class='MuiTypography-root sc-fzplgP iNPcrX MuiTypography-body1']"
    
    # create list of all values - ignore Beta
    data = [d.text.replace('Beta', '') for d in driver.find_elements_by_xpath(ctDataXpath)]
    
    # xpath for all ratings, contains() has unique string
    # ratingsXpath = "//div[starts-with(@class, 'MuiBox-root jss') and contains(@class, 'sc-fzonjX fnCkZA')]"
    ratingsXpath = "//div[contains(@class, 'sc-fzqzEs ghDBgq')]"

    res = driver.find_elements_by_xpath(ratingsXpath)
    if len(res) != 5 :
        print('Error:', len(res), 'ratings found instead of 5. The web page structure may have changed!')
        exit(-1)

    ratings = [d.text for d in res]

    
    # # create dataframe, returned but unused
    # pandaData = {'Value':data, 'Rating':ratings}
    # df = pd.DataFrame(pandaData, index=['Daily New Cases', 'Infection Rate', 'Positive Test Rate', 
    #                                     'ICU Headroom Used', 'Contacts Traced'])
    
    # get string containing date of last data update
    lastUpdateXpath = "//p[@class='MuiTypography-root sc-qQmou jqDvEh MuiTypography-body1']"
    lastUpdate = driver.find_element_by_xpath(lastUpdateXpath).text.lstrip('Last Updated ')
    
    driver.close()

    # convert date to previous form (page was updated)
    try:
        pageDateFmt = '%B %d, %Y'
        newDateFmt = '%m/%d/%Y'
        lastUpdate = datetime.datetime.strptime(lastUpdate, pageDateFmt).strftime(newDateFmt)
    except:
        raise Exception('Date format changed on website')
        
    # create list of data to be returned
    ctData = [lastUpdate]
    #indices in data/ratings match for category, iterate through both to populate new list of data
    for i in range(len(data)):
        ctData.append(data[i])
        ctData.append(ratings[i])
    
    ctData.append(overallRisk)
    ctData.append(threatLevel[0]) # small threat indicator (i.e. 'Slow disease growth')
    ctData.append(threatLevel[1]) # longer expanatory string
    ctData.append(state)

    
    # newDataDict = {'updated':lastUpdate, 'risk':overallRisk, 'threat level':threatLevel[0], 
    #                 'threat string':threatLevel[1], 'state':state}
   
    # info = ['NC value', 'NC rating', 'IR value', 'IR rating', 'PTR value', 'PTR rating', 
    #         'ICU value', 'ICU rating', 'CT value', 'CT rating']
    
    # infoIndex = 0
    # for i in range(len(data)):
    #     newDataDict[info[infoIndex]] = data[i]
    #     newDataDict[info[infoIndex + 1]] = ratings[i]
    #     infoIndex += 2
    
    return ctData


def writeNewFile(output):
    
    with open(file, 'w') as writeFile:
        writeFile.write('Last Updated\tDaily New Cases\tInfection Rate\tPos Test Rate\tICU Headroom\tContacts Traced\tRisk\tThreat Level\n')
        writeFile.write('\n' + ('\t').join(output[:-2]))    


def getPrevData(file):

    newLineFlag = False # issue of auto creation of \n when modifying text file for testing
    
    # get last line of file (most recent data)
    line = []
    with open(file) as inFile:
        inFile.seek(0, 2) # seek to file end
        index = inFile.tell() # get index of last character in line
        index = index - 1
        inFile.seek(index) # go to last character in file
        
        # if file ends with \n skip
        if inFile.read(1) == '\n':
            index = index - 1
            inFile.seek(index)
            newLineFlag = True
        # loop till end of last line (\n character) / add each character to list
        while inFile.read(1) != '\n':
            line.append(inFile.read(1))
            index = index - 1
            inFile.seek(index)
            
        line.append(inFile.read(1))
                    
    line.reverse()
    line = ('').join(line) # reverse list and combine to string
    return [line.strip('\n ').split('\t'), newLineFlag]

def getPrevWeek(file, currentDay):
    dateFormat = '%m/%d/%Y'
    #get day of year number, easier to track days when crossing over months
    currentDayNum = datetime.datetime.strptime(currentDay, dateFormat).timetuple().tm_yday
    
    with open(file) as inFile:
        
        inFile.readline() # skip first two lines
        inFile.readline()

        data = inFile.readline().strip('\n').split('\t')
        testDayNum = datetime.datetime.strptime(data[0], dateFormat).timetuple().tm_yday

        if testDayNum > currentDayNum - 7: # test enough data in file
            raise Exception('Data not present from a week ago')
        elif testDayNum == currentDayNum - 7: # if first entry is 7 days ago
            return data
        
        for line in inFile: # iterate through rest of file
            data = line.strip('\n').split('\t')
            testDayNum = datetime.datetime.strptime(data[0], dateFormat).timetuple().tm_yday
            if testDayNum >= currentDayNum - 7: # go until day in file is either
                break
    return data
        

# compare new and previous data (excluding contact tracing)
def compareData (new, prev, testValue, increaseOnly): # new/prev[0] is value, [1] is risk level
    
     # dict assigning numbers to threat, higher number higher threat
    testingDict = {'Low': 0, 'Medium': 1, 'High': 2, 'Critical': 3}
    
    if increaseOnly: # if only tracking increases in threat, 0 or 1 returned to track whether increase in threat
        if testingDict[prev[1]] >= testingDict[new[1]]: # if prev threat worse or equal to new
            return [0, testValue + ': ' + new[0] + ' (' + new[1] + ')']
        else: # return warning string 
            return [1, 'The risk level for <b>' + testValue + '</b> has <b>increased</b> from <b>' + \
                    prev[1] + ' (' + prev[0] + ')</b> to <b>' + new[1] + ' (' + new[0] + ')</b>']            
    else: # html generation if not only linked to increase
        if testingDict[prev[1]] == testingDict[new[1]]:
            return 'There is <b>no change</b> in the <b>' + new[1] +'</b> risk level based on \
                <b>' + testValue + ' (' + new[0] + ')</b>'
        elif testingDict[prev[1]] < testingDict[new[1]]:
            return 'The risk level for <b>' + testValue + '</b> has <b>increased</b> from <b>' + prev[1] + \
                ' (' + prev[0] + ')</b> to <b>' + new[1] + ' (' + new[0] + ')</b>'
        else:
            return 'The risk level for <b>' + testValue + '</b> has <b>decreased</b> from <b>' + prev[1] + \
                ' (' + prev[0] + ')</b> to <b>' + new[1] + ' (' + new[0] + ')</b>'


# compare new and previous contact tracing data, higher value is ideal
def compareContactTrace (new, prev, increaseOnly): # new/prev[0] is value, [1] is risk level

    # dictionary assigning numbers to threat, higher number higher threat    
    testingDict = {'High': 0, 'Medium': 1, 'Low': 2} 
    
    if increaseOnly: # if only tracking increase in threat, 0 or 1 to capture increase occurance
        # if new less than prev, reduction in tracing / increase in threat
        if testingDict[prev[1]] >= testingDict[new[1]]: # no increase
            return [0, 'Contact Tracing: ' + new[0] + ' (' + new[1] + ')'] # return current values
        else: # increase in threat, return warning string with new and previous values
            return [1, '<b>Contact Tracing</b> coverage has <b>decreased</b> from <b>' + prev[1] + \
                    ' (' + prev[0] + ')</b> to <b>' + new[1] + ' (' + new[0] + ')</b>']            
    else: # generate html for all changes
        if testingDict[prev[1]] == testingDict[new[1]]:
            return 'There is <b>no change</b> in the <b>' + new[1] + '</b> coverage by \
                <b>contact tracing (' + new[0] + ')</b>'
        elif testingDict[prev[1]] > testingDict[new[1]]:
            return '<b>Contact tracing</b> coverage has <b>increased</b> from <b>' + prev[1] + ' (' + \
                prev[0] + ')</b> to <b>' + new[1] + ' (' + new[0] + ')</b>'
        else:
            return '<b>Contact tracing</b> coverage has <b>decreased</b> from <b>' + prev[1] + ' (' + \
                prev[0] + ')</b> to <b>' + new[1] + ' (' + new[0] + ')</b>'


# compare overall COVID risk
def compareCovidThreatLevel (new, prev):
    
    # dict with numbers to represent words
    testingDict = {'Low': 0, 'Medium': 1, 'High': 2, 'Critical': 3}
    newRisk = new[0] # risk to be compared with prev
    threatLevel = new[1] # string describing risk level
    
    if testingDict[prev] == testingDict[newRisk]:
        return '<b>No change in overall COVID risk</b>.  Threat level is <b>' + \
            newRisk + '</b><br><br>' + threatLevel
    elif testingDict[prev] > testingDict[newRisk]:
        return '<b>Overall COVID risk</b> has <b>decreased</b> from <b>' + prev + \
            '</b> to <b>' + newRisk + '</b><br><br>' + threatLevel
    else:
        return '<b>the overall COVID risk of COVID-19 has increased from ' + prev + \
            ' to ' + newRisk + '</b>. ' + threatLevel + '.'
    
    
# current data list, previous data list, state abbreviation, web page, bool to only track threat increases
def generateHTML (output, prevData, inputState, page, increaseOnly):
    
    # get comparison strings for each category (excluding contact tracing) -- klunky arg passing
    overallThreat = compareCovidThreatLevel ([output[11], output[13]], prevData[11])
    newCases = compareData([output[1], output[2]], [prevData[1], prevData[2]], 'Daily New Cases', increaseOnly)
    infectionRate = compareData([output[3], output[4]], [prevData[3], prevData[4]], 'Infection Rate', increaseOnly)
    posTestRate = compareData([output[5], output[6]], [prevData[5], prevData[6]], 'Positive Test Rate', increaseOnly)
    icuHeadroom = compareData([output[7], output[8]], [prevData[7], prevData[8]], 'ICU Headroom', increaseOnly)
    # get comparison string for contact tracing
    contactTraced = compareContactTrace([output[9],output[10]], [prevData[9],prevData[10]], increaseOnly)
    
    # get list of all increased threat levels (if function returned 1)
    increased = [i[1] for i in [newCases, infectionRate, posTestRate, icuHeadroom, contactTraced] if i[0] == 1]
    # if value has increased    
    if len(increased) > 0: # if increase in threat - valid for both T/F increaseOnly
        # get list of all threat levels without increase (function returned 0)
        noIncrease = [i[1] for i in [newCases, infectionRate, posTestRate, icuHeadroom, contactTraced] if i[0] == 0]
        # generate html
        with open(page, 'w') as writeFile:
            #writeFile.write('<h1>Daily Update Tracker for COVID</h1>')
            writeFile.write('<h3>EIDA/Covid in CT Alert (' + 
                    date.today().strftime('%m/%d/%Y') +')</h3>')

#            writeFile.write('<p>Current data updated on ' + output[0] + 
#                            ' -- Previous data updated on ' + prevData[0] + '</p>')
            writeFile.write('<p>Based on data provided by CovidActNow (<a href = "https://covidactnow.org/">https://covidactnow.org/</a>), ' + overallThreat + '</p>')

            # print description of metrics
            s = """
            CovidActNow tracks risk across 5 categories:
            <ul>
            <li>Daily new cases: this is the daily number of new cases per 100,00 individuals, averaged over the last week; a value > 1 indicates that the virus is currently not being contained. </li>
            <li>Infection rate: this is the average number of people that an infected individual infects; a value < 1 indicates that the number of infections is decreasing.</li>
<li>Positive test rate: this is the percent of people tested who are positive for COVID-19; experts recommend that this value be < 3% to ensure that a sufficient amount of testing is occuring.</li>
<li>ICU headroom used: this is the percent of ICU beds in use; a value < 50% indicates that there is sufficient ICU capacity in the event of another wave of infections.</li>
<li>Tracers hired: this is the percent of contacts traced within 48 hours; a value over 90% is recommended for COVID to be contained, and indicates that enough tracers have been hired.</li>
</ul>
            """

            writeFile.write(s)
            #writeFile.write('<p>' + overallThreat + '</p>')
            writeFile.write('<p><b>In the past day there has been an increase in risk for the following categories:</b></p><ul>')
            [writeFile.write('<li>' + i + '</li>') for i in increased] # unordered list for increased data
            writeFile.write('</ul><p>The values for the other categories are as follows:</p>')
            writeFile.write('<ul>') # unordered list with non-increased data
            [writeFile.write('<li>' + i + '</li>') for i in noIncrease]
            writeFile.write('</ul>')

            link = 'https://covidactnow.org/state/' + inputState + '/'

            if output[14] == 'Connecticut' :
                writeFile.write('<p>You can view the current scorecard for ' + output[14] + 
                    ' by visiting: <a href="' + link + '">' + link + '</a>' +  
                    ' or our COVID in CT page at ' +
                    '<a href = "https://eida.easternct.edu/shiny/app/covid-ct">https://eida.easternct.edu/shiny/app/covid-ct</a>.') 
            else :
                writeFile.write('<p>You can view the current scorecard for ' + output[14] + 
                    ' by visiting <a href="https://covidactnow.org/embed/us/' + 
                    inputState + '">link</a>') # link to scorecard for state

        print('\n\nWeb page generated - increase in threat detected')
    elif not increaseOnly: # if no increase in threat and increaseOnly == False
        testingDict = {'Low': 0, 'Medium': 1, 'High': 2, 'Critical': 3}
        if testingDict[prevData[11]] > testingDict[output[11]]:
            compareString = 'decrease from last week'
        else:
            compareString = 'no change from last week'
        with open(page, 'w') as writeFile:
            writeFile.write('<h1>Daily Update Tracker for COVID</h1>')
            writeFile.write('<p>Current data updated on ' + output[0] + 
                            ' -- Previous data updated on ' + prevData[0] + '</p>')
            writeFile.write('<p>According to CovidActNow, the current COVID threat level is ' + output[11] + 
                            ' (' + compareString + '). For more information, see the attached scorecard \
                                or visit <a href="https://covidactnow.org/embed/us/' + inputState + 
                                '">https://covidactnow.org/embed/us/' + inputState + '</a>')
        print('Web page generated - no increase in threat')
                
    else:
        print('No web page generated - no increase in threat')
        
        
def setIncreaseOnly(updateType):
    if updateType.lower() == 'daily':
        return True
    elif updateType.lower() == 'weekly':
        return False
    else:
        raise argparse.ArgumentTypeError('update-type argument must be daily or weekly')
        

# arguments for command line execution
ap = argparse.ArgumentParser(description='Extract info from covidactnow, generate HTML, capture data')
ap.add_argument('file', help = 'file containing previous covid data or a new file to create')
ap.add_argument('page', help = 'HTML file to be created')
ap.add_argument('inputState', help = 'state abbreviation')
ap.add_argument('update-type', help = 'set update interval (daily|weekly)')
# default uses path linked to python install, if driver not found insert path
ap.add_argument('geckoDriverPath', nargs='?', default=None, help = 'optional path for geckodriver')

# print help if no arguments are provided
if len(sys.argv)==1:
    ap.print_help(sys.stderr)
    sys.exit(1)

args = vars(ap.parse_args())

file = args['file']
page = args['page']
inputState = args['inputState']
updateType = args['update-type']
geckoPath = args['geckoDriverPath']

increaseOnly = setIncreaseOnly(updateType)

output = getWebData(inputState, geckoPath)

if os.path.isfile(file): # if file with covid data exists
    response = getPrevData(file)
    prevData = response[0] # list with previous data
    newLineFlag = response[1] # flag indicating whether prev line ends with \n
    
    if prevData[0] == output[0]: # if last updated dates match
        print("Data up to date")
    else:
        with open(file, 'a') as writeFile: # append to eof
            if not newLineFlag:
                writeFile.write('\n')
            writeFile.write(('\t').join(output[:-2])) # skip state and full risk string
            
        if increaseOnly == True: # if daily update generate html only if increase
            testingDict = {'Low': 0, 'Medium': 1, 'High': 2, 'Critical': 3}
            if testingDict[output[11]] > testingDict[prevData[11]]:
                generateHTML(output, prevData, inputState, page, increaseOnly)
            else:
                print('No web page generated - no increase in overall threat level')
        else: # if weekly update, get previous week data and generate html
            prevData = getPrevWeek(file, output[0])
            generateHTML(output, prevData, inputState, page, increaseOnly)
            
else:
    writeNewFile(output)
    print('New file created')
