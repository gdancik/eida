#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jul 17 14:54:39 2020

@author: kewilliams

usage: python_covidactnow.py [-h] dataFile page inputState increaseOnly [geckoDriverPath]
"""

from selenium import webdriver
from selenium.webdriver.firefox.options import Options
import pandas as pd
import os
import time
import argparse
import sys

def getWebData (inputState, geckoPath):
    
    options = Options()
    options.headless = True
    
    if not geckoPath:
        driver = webdriver.Firefox(options = options)
    else:
        driver = webdriver.Firefox(options = options, executable_path=geckoPath)
    
    driver.get('https://www.covidactnow.org/us/' + inputState)
    
    time.sleep(1)
    
    threatLevelXpath = "//div[@class='MuiBox-root jss20 sc-pRTZB eBhZMp']"
    threatLevel = driver.find_element_by_xpath(threatLevelXpath)
    threatLevel = threatLevel.text.split('\n')[1:]
    # condense threat level string, arguably only need first sentence or up to first comma
    threatLevel[1] = threatLevel[1].replace(',', '.').split('.')[0]
    
    overallRiskXpath = "//div[@class='sc-fznAgC dSEOxJ']"
    overallRisk = driver.find_element_by_xpath(overallRiskXpath).text.split('\n')
    state = overallRisk[0] # get state string
    overallRisk = overallRisk[2] # overwrite risk to string containing risk
    
    ctDataXpath = "//p[@class='MuiTypography-root sc-fzoWqW kjrSyq MuiTypography-body1']"
    
    data = driver.find_elements_by_xpath(ctDataXpath)
    data = [d.text.replace('Beta', '') for d in data]
    
    dailyNewCasesRatingXpath = "//div[@class='MuiBox-root jss42 sc-fzonjX fnCkZA']"
    infectionRatingXpath = "//div[@class='MuiBox-root jss44 sc-fzonjX fnCkZA']"
    posTestRatingXpath = "//div[@class='MuiBox-root jss46 sc-fzonjX fnCkZA']"
    icuRatingXpath = "//div[@class='MuiBox-root jss48 sc-fzonjX fnCkZA']"
    contactTraceRatingXpath = "//div[@class='MuiBox-root jss50 sc-fzonjX fnCkZA']"

    dailyNewCasesRating = driver.find_element_by_xpath(dailyNewCasesRatingXpath).text
    infectionRating = driver.find_element_by_xpath(infectionRatingXpath).text
    posTestRating = driver.find_element_by_xpath(posTestRatingXpath).text
    icuRating = driver.find_element_by_xpath(icuRatingXpath).text
    contactTraceRating = driver.find_element_by_xpath(contactTraceRatingXpath).text

    ratings = [dailyNewCasesRating, infectionRating, posTestRating, icuRating, contactTraceRating]
    
    pandaData = {'Value':data, 'Rating':ratings}
    df = pd.DataFrame(pandaData, index=['Daily New Cases', 'Infection Rate', 'Positive Test Rate', 
                                        'ICU Headroom Used', 'Contacts Traced'])
    
    lastUpdateXpath = "//p[@class='MuiTypography-root sc-fzqMdD fZQoNm MuiTypography-body1']"
    lastUpdate = driver.find_element_by_xpath(lastUpdateXpath).text.lstrip('Last Updated ')
    
    driver.close()
    
    ctData = [lastUpdate]
    for i in range(len(data)):
        ctData.append(data[i])
        ctData.append(ratings[i])
    
    ctData.append(overallRisk)
    ctData.append(threatLevel[0])
    ctData.append(threatLevel[1])
    ctData.append(state)

    return df, ctData


def getPrevData(file):
    
    if not os.path.isfile(file): # create new file if does not exist
        with open(file, 'w') as writeFile:
            writeFile.write('Last Updated\tDaily New Cases\tInfection Rate\tPos Test Rate\tICU Headroom\tContacts Traced\tRisk\tThreat Level\n')
            writeFile.write('\n' + ('\t').join(output[:-1]))
    
    else: # update and perform testing on file
        
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
        
    return None # if new file was created


def compareData (new, prev, testValue, increaseOnly): # new/prev[0] is value, [1] is risk level
    
    testingDict = {'Low': 0, 'Medium': 1, 'High': 2, 'Critical': 3}
    
    if increaseOnly:
        if testingDict[prev[1]] >= testingDict[new[1]]:
            return [0, testValue + ' - ' + new[1] + ' (' + new[0] + ')']
        else:
            return [1, 'The risk level for <b>' + testValue + '</b> has <b>increased</b> from <b>' + \
                    prev[1] + ' (' + prev[0] + ')</b> to <b>' + new[1] + ' (' + new[0] + ')</b>']            
    else:
        if testingDict[prev[1]] == testingDict[new[1]]:
            return 'There is <b>no change</b> in the <b>' + new[1] +'</b> risk level based on \
                <b>' + testValue + ' (' + new[0] + ')</b>'
        elif testingDict[prev[1]] < testingDict[new[1]]:
            return 'The risk level for <b>' + testValue + '</b> has <b>increased</b> from <b>' + prev[1] + \
                ' (' + prev[0] + ')</b> to <b>' + new[1] + ' (' + new[0] + ')</b>'
        else:
            return 'The risk level for <b>' + testValue + '</b> has <b>decreased</b> from <b>' + prev[1] + \
                ' (' + prev[0] + ')</b> to <b>' + new[1] + ' (' + new[0] + ')</b>'

        
def compareContactTrace (new, prev, increaseOnly): # new/prev[0] is value, [1] is risk level
    
    testingDict = {'High': 0, 'Medium': 1, 'Low': 2}
    
    if increaseOnly:
        if testingDict[prev[1]] >= testingDict[new[1]]:
            return [0, 'Contact Tracing - ' + new[1] + ' (' + new[0] + ')']
        else:
            return [1, '<b>Contact Tracing</b> coverage has <b>decreased</b> from <b>' + prev[1] + \
                    ' (' + prev[0] + ')</b> to <b>' + new[1] + ' (' + new[0] + ')</b>']            
    else:
        if testingDict[prev[1]] == testingDict[new[1]]:
            return 'There is <b>no change</b> in the <b>' + new[1] + '</b> coverage by \
                <b>contact tracing (' + new[0] + ')</b>'
        elif testingDict[prev[1]] > testingDict[new[1]]:
            return '<b>Contact tracing</b> coverage has <b>increased</b> from <b>' + prev[1] + ' (' + \
                prev[0] + ')</b> to <b>' + new[1] + ' (' + new[0] + ')</b>'
        else:
            return '<b>Contact tracing</b> coverage has <b>decreased</b> from <b>' + prev[1] + ' (' + \
                prev[0] + ')</b> to <b>' + new[1] + ' (' + new[0] + ')</b>'


def compareCovidThreatLevel (new, prev):
    
    testingDict = {'Low': 0, 'Medium': 1, 'High': 2, 'Critical': 3}
    newRisk = new[0]
    threatLevel = new[1]
    
    if testingDict[prev] == testingDict[newRisk]:
        return '<b>No change in overall COVID risk</b>.  Threat level is <b>' + \
            newRisk + '</b><br><br>' + threatLevel
    elif testingDict[prev] > testingDict[newRisk]:
        return '<b>Overall COVID risk</b> has <b>decreased</b> from <b>' + prev + \
            '</b> to <b>' + newRisk + '</b><br><br>' + threatLevel
    else:
        return '<b>Overall COVID risk</b> has <b>increased</b> from <b>' + prev + \
            '</b> to <b>' + newRisk + '</b><br><br>' + threatLevel
    
# current data list, previous data list, state abbreviation, web page, bool to only track threat increases
def trackChanges (output, prevData, inputState, page, increaseOnly):
    
    # get comparison strings for each category (excluding contact tracing) -- klunky arg passing
    overallThreat = compareCovidThreatLevel ([output[11], output[13]], prevData[11])
    newCases = compareData([output[1], output[2]], [prevData[1], prevData[2]], 'Daily New Cases', increaseOnly)
    infectionRate = compareData([output[3], output[4]], [prevData[3], prevData[4]], 'Infection Rate', increaseOnly)
    posTestRate = compareData([output[5], output[6]], [prevData[5], prevData[6]], 'Positive Test Rate', increaseOnly)
    icuHeadroom = compareData([output[7], output[8]], [prevData[7], prevData[8]], 'ICU Headroom', increaseOnly)
    # get comparison string for contact tracing
    contactTraced = compareContactTrace([output[9],output[10]], [prevData[9],prevData[10]], increaseOnly)
    
    if not increaseOnly:
    
        # generate HTML
        with open(page, 'w') as writeFile:
            
            writeFile.write('<h1>Daily Update Tracker for COVID</h1>')
            writeFile.write('<p>Current data updated on ' + output[0] + 
                            ' -- Previous data updated on ' + prevData[0] + '</p>')
            writeFile.write('<p>' + overallThreat + '</p>')
            writeFile.write('<ul>')
            [writeFile.write('<li>' + i + '</li>') for i in [newCases, infectionRate, posTestRate, icuHeadroom, contactTraced]]
            writeFile.write('</ul>')
            writeFile.write('<p>You can view the current scorecard for ' + output[14] + 
                ' by clicking here: <a href="https://covidactnow.org/embed/us/' + 
                inputState + '">link</a>')
            
    else: # if only printing increased threat
        # get list of all increased threat levels
        increased = [i[1] for i in [newCases, infectionRate, posTestRate, icuHeadroom, contactTraced] if i[0] == 1]
        # if value has increased    
        if len(increased) > 0:
            noIncrease = [i[1] for i in [newCases, infectionRate, posTestRate, icuHeadroom, contactTraced] if i[0] == 0]
            with open(page, 'w') as writeFile:
                writeFile.write('<h1>Daily Update Tracker for COVID</h1>')
                writeFile.write('<p>Current data updated on ' + output[0] + 
                                ' -- Previous data updated on ' + prevData[0] + '</p>')
                writeFile.write('<p>' + overallThreat + '</p>')
                writeFile.write('<p>There has been an increase in risk for the following categories:</p><ul>')
                [writeFile.write('<li>' + i + '</li>') for i in increased]
                writeFile.write('</ul><p>The risks for the other categories are as follows:</p>')
                writeFile.write('<ul style="list-style-type:square;">')
                [writeFile.write('<li>' + i + '</li>') for i in noIncrease]
                
                writeFile.write('<p>You can view the current scorecard for ' + output[14] + 
                    ' by clicking here: <a href="https://covidactnow.org/embed/us/' + 
                    inputState + '">link</a>')
            print('Web page generated')
        else:
            print('No page generated - no increase in threat')
            

ap = argparse.ArgumentParser(description='Extract info from covidactnow, generate HTML, capture data')
ap.add_argument('file', help = 'file containing previous covid data or a new file to create')
ap.add_argument('page', help = 'HTML file to be created')
ap.add_argument('inputState', help = 'state abbreviation')
ap.add_argument('increaseOnly', help = 'flag indicating whether to only generate HTML if threat increase')
ap.add_argument('geckoDriverPath', nargs='?', default=None, help = 'optional path for geckodriver')

# print help if no arguments are provided
if len(sys.argv)==1:
    ap.print_help(sys.stderr)
    sys.exit(1)

args = vars(ap.parse_args())

file = args['file']
page = args['page']
inputState = args['inputState']
increaseOnly = args['increaseOnly']
geckoPath = args['geckoDriverPath']

response = getPrevData(file)
data = getWebData(inputState, geckoPath)
# df = data[0]
output = data[1]


if response is not None: # if not new file
    prevData = response[0] # list with previous data
    newLineFlag = response[1] # flag indicating whether prev line ends with \n
    
    if prevData[0] == output[0]: # if last updated dates match
        print("Data up to date")
    else:
        with open(file, 'a') as writeFile: # add to eof
            if not newLineFlag:
                writeFile.write('\n')
            writeFile.write(('\t').join(output[:-2])) # skip state and full risk string
                
        trackChanges(output, prevData, inputState, page, increaseOnly)
else:
    print('New file created')