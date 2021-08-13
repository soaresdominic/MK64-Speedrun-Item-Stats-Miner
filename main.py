'''
Project: MK64 item stats miner
Purpose: to retreive and analyze item box counts / stats during full game skips speedruns
Description:
Loop over all videos in folder and analyze the frames sequentially to determine what items are given
by the item roulette. Collect stats on Place, Item, Course, Frame, Video. Append these stats to a file - 
append these stats so if the program stops working it retains the stats
Assumptions:
 - input videos are 1080p, same format as current vids as of 8/12/21
 - videos don't start during a run

Usage (preferred):
-Navigate to root folder in powershell
-python main.py

Flowchart:
1. Search for a course start screen - every 80 frames check if it relates to a start screen
    - you are at the starting line not moving for at least 80 frames
> Found course start screen
> Now in course
2. Search for an item - every 25 frames - that many frames in fastest item roulette
2.1 Also be searching for black screen
        -time for black screen, console reset (65 frames), course finish (73 frames), or menu -> restart or exit (40 frames)
> Found black screen
    > Out of course, go to 1.
> Found item
3. Try to find first blank item in roulette - indicates the last item seen is the item given
> Found Blank Item
> Record the last item put into item roulette list
3.1 If item was a Boo - do the complicated find Boo item procedure, then go to 2.
4. Try to find No item - indicating it was used and to go back to trying to find a new roulette
4.1 Check that we are not in a new roulette, since item box at top of screen doesnt go away if
    item is spammed into another box
> Found No item
> Go to 2
> > Found we're in new roulette
> > Go to 3.


TO DO LIST:
 - if we find wario stadium or frappe snowland - skip until black screen since there will never be an item pickup

 - recognize time trials runs to be able to skip them so vids dont have to be trimmed?
 - Record the number of console resets?
 - Record the number of speedrun resets?
'''

import cv2
import numpy as np
from matplotlib import pyplot as plt
import csv
import setup
import os
import datetime


class Gamestate:
    '''
    place = 8  #current place in the race
    count = 0  #Frame count of current vid
    itemRoulette = []  #holds list of names of items that we last found in a roulette
    newItemRoulette = [None, None]  #holds the temporary 2 potential items from adjacent frames to signify in new roulette
    
    inNewItemRoulette = False  #when trying to find no item, if newItemRoulette has two different items
    foundBlankItem = False  #found first blank item in roulette
    goToSecondFrame = True  #when trying to see if we're in a new roulette, change the list value that is updated

    currentCourseIndex = 0  #current / last course index
    currentCourse = ""   #current course string

    foundAnItem = False  #Found first item signifying we're in a roulette
    foundNoItem = False  #after finding the given item, trying to find no item visible
    foundGivenItem = False  #when we determine the item given
    foundNoBoo = False  #When we are trying to find no boo after getting one

    blankItemIndex = i   #index of the blankitem in the items list, get it dynamically
    '''

    def __init__(self):
        self.place = 8
        self.count = 0
        self.itemRoulette = []
        self.newItemRoulette = [None,None]
        
        self.inNewItemRoulette = False
        self.foundBlankItem = False
        self.goToSecondFrame = True

        self.currentCourseIndex = 0
        self.currentCourse = ""

        self.foundAnItem = False
        self.foundNoItem = False  #only used after we get an item, so default is False
        self.foundGivenItem = False
        self.foundNoBoo = False  #this is true after we get a boo and then find a frame without it
        
        for i, item in enumerate(items):
            if item[0] == "BlankItem":
                self.blankItemIndex = i
                break
    



def main():
    #For each video we have in the directory of videosToAnalyze
    videosDirectory = './videosToAnalyze/'
    localSetup()  #grab all the pics and things for image matching
    with open('./stats/ItemStats.csv','a') as f:
        writer = csv.writer(f)
        writer.writerow(['Starting analysis on all videos - ' + str(datetime.datetime.now())])
    for videoFileName in os.listdir(videosDirectory):
        global videoName
        videoName = videoFileName
        try:
            vidcap = cv2.VideoCapture(videosDirectory + videoFileName)
        except:
            print("Video " + videoFileName + " could not be read")
            continue

        with open('./stats/ItemStats.csv','a') as f:
            writer = csv.writer(f)
            writer.writerow(['Starting analysis on video: ' + videoName])

        print("Analyzing video " + videoFileName)
        gamestate = Gamestate()
        frameNum = 0  #debug 5915 #12749 #32350 #5400 #10141 #5000  #13000

        gamestate.count = frameNum

        #Loop to read images from video
        while True:
            vidcap.set(cv2.CAP_PROP_POS_FRAMES, frameNum)   #sets the frame to read
            success,image = vidcap.read()
            if not success: 
                break

            #if current course is empty, loop until we find one
            if gamestate.currentCourse == "":
                findCourse(image, gamestate)
                if gamestate.currentCourse == "":  #didnt find one, skip 80 frames
                    frameNum += 80
                    gamestate.count += 80
                else:
                    continue
            #if we're in a course and we have not found an item - try to find an item or a black screen
            elif gamestate.foundAnItem == False and gamestate.foundGivenItem == False:
                findAnItem(image, gamestate)
                if gamestate.foundAnItem == False:  #didnt find item
                    frameNum += 25  #based on fastest roulette (on royal raceway)
                    gamestate.count += 25
                else:
                    continue
            #if we're in a course and we have found an item
            elif gamestate.foundAnItem == True and gamestate.foundGivenItem == False and gamestate.foundBlankItem == False:
                findFirstBlankInRoulette(image, gamestate)
                if gamestate.foundBlankItem == False:  #still havent found the first blank
                    frameNum += 4   #5 frames of blanks so 4 should always hit
                    gamestate.count += 4
                else:  #found the blank item
                    continue
            #if we're in a course and we have found the blank item, go backwards until we hit the last item
            elif gamestate.foundAnItem == True and gamestate.foundGivenItem == False:
                findGivenItem(image, gamestate)
                if gamestate.foundGivenItem == False:  #still havent nailed down the given item
                    frameNum -= 1
                    gamestate.count -= 1
                else:  #found the given item
                    continue
            #if we got a boo, find the item it gives us / try to find no boo, then go backwards then forwards
            elif gamestate.foundGivenItem == True and itemStats[-1][1] == 'Boo' and gamestate.foundNoBoo == False:
                findBooItem(image, gamestate)
                if gamestate.foundNoBoo == False:
                    frameNum += 5*30  #skip ahead five seconds
                    gamestate.count += 5*30
                else:
                    frameNum -= 5*30  #skip back once
                    gamestate.count -= 5*30
                    continue
            #If we just got a boo, find the item the boo gives you
            #Once we record this next item, this elif will no longer hit
            #THIS SECOND 1 FOR INDEXING IS IMPORTANT IF THE ITEMSTATS LIST IS CHANGED
            elif gamestate.foundGivenItem == True and itemStats[-1][1] == 'Boo' and gamestate.foundNoBoo == True:
                findBooItem(image, gamestate)
                #First check if the boo gave us no item - we want to skip 86 frames if it did
                #91 frames of time from first frame of first blink to last frame of BOO item on screen
                #This could be changed - but this makes sure we dont find a boo as a normal item if we
                #   enter the find item loop too early
                if gamestate.foundAnItem == False and gamestate.foundGivenItem == False:
                    frameNum += 91
                    gamestate.count += 91
                if itemStats[-1][1] == 'Boo':
                    frameNum += 5
                    gamestate.count += 5
                else:  #found the boo item
                    continue
            #if we just determined the given item
            #try to find no item, black screen, or determine if we're in another item roulette
            #If we're in another roulette, cant just look every x frames since the same item could
            #   be the frame we found in the new roulette, but since its the same it wont register as new
            #Do pairs of frames every 20 frames to see if they have different items
            elif gamestate.foundGivenItem == True:
                findNoItem(image, gamestate)
                if gamestate.foundNoItem == False:  #still have item in inventory
                    #print(set(gamestate.itemRoulette), gamestate.itemRoulette)
                    #Every 20 frames do two consequtive frames to see if we're in another roulette
                    #if items are different and not None
                    #DO I CARE ABOUT BLANKS AND TWO MUSHROOMS HERE??????????? idk
                    #print(gamestate.newItemRoulette)
                    #Double Mushrooms signify using a triple mushroom, so rule that out
                    if gamestate.newItemRoulette[0] != gamestate.newItemRoulette[1] and \
                       gamestate.newItemRoulette[0] is not None and \
                       gamestate.newItemRoulette[1] is not None and \
                       gamestate.newItemRoulette[0] != "DoubleMushrooms" and \
                       gamestate.newItemRoulette[1] != "DoubleMushrooms":
                        gamestate.foundAnItem = True
                        gamestate.foundGivenItem = False
                        gamestate.goToSecondFrame = True
                        gamestate.newItemRoulette = [None, None]
                        print("Back into item roulette")
                    else:
                        #should be able to do 20 frames, gives enough time if we go into new
                        #roulette for us to realize that between the 20-25th last 5 frames
                        #of the roulette
                        if gamestate.goToSecondFrame == True:
                            frameNum += 1
                            gamestate.count += 1
                        else:
                            frameNum += 19
                            gamestate.count += 19
                            gamestate.newItemRoulette = [None, None]

                        #Then change whether to do +1 or +19 next
                        if gamestate.goToSecondFrame == True:
                            gamestate.goToSecondFrame = False
                        else:
                            gamestate.goToSecondFrame = True
                else:  #found no item
                    continue

            #Very last thing for EVERY frame inside a course is check for black screen.
            #Reset all vars in function if we find it
            if gamestate.currentCourse != "":
                findBlackScreen(image, gamestate)
        #At the end of the current vid
        print("Done!")
        with open('./stats/ItemStats.csv','a') as f:
            writer = csv.writer(f)
            writer.writerow(['Done with analysis on video: ' + videoName])
    with open('./stats/ItemStats.csv','a') as f:
        writer = csv.writer(f)
        writer.writerow(['Done with analysis on all videos - ' + str(datetime.datetime.now())])



#Although it doesnt seem like it, there is a lot of variance in the color of the places (capture card related?)
#enough to where the darkest 1st has the same color as the brightest 2nd
def getPlace(image, gamestate):
    #First we can rule out 8th, since it's very common, with basic color detection
    image_8th = image[865:879, 728:739]
    image_8th = cv2.cvtColor(image_8th, cv2.COLOR_BGR2GRAY)
    #print(image_8th)
    if min(min(image_8th, key=min)) >= 90 and max(max(image_8th, key=max)) <= 110:
        gamestate.place = 8
        return

    #Now do matching for other places
    #Masking took a while to figure out, it may not be perfect
    image_place = image[700:980, 600:930]  #[650:880, 750:930]
    #dont know if inversion helps - it seems to for black screens
    image_place = 255-image_place
    maxs = []
    for it, place in enumerate(places[:-1]):
        template = place[1]
        template = 255-template
        method = place[2]
        mask = masks[it]
        res = cv2.matchTemplate(image_place, template, method, None, mask=mask)  #with masking
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
        #print(max_val)
        maxs.append(max_val)
    if max(maxs) > .95:
        gamestate.place = maxs.index(max(maxs)) + 1   #index of the min value + 1
        print(gamestate.count, "Current place:", gamestate.place)
    else:
        gamestate.place = 0
        print(gamestate.count, "Could not determine place. Place set to 0")



def findCourse(image, gamestate):
    img_playArea = image[:, 560:]
    if gamestate.currentCourseIndex == 0:
        potentialNextCourses = [0,1,4,8,12]
    else:
        potentialNextCourses = [0, gamestate.currentCourseIndex + 1]

    print(gamestate.count, "Searching for course...")
    for indexVal in potentialNextCourses:  #for each of the selected potential next courses
        course = courses[indexVal]
        template = course[1]
        if course[0] == "BansheeBoardwalk":  #very dark, inverting seems to help
            template = 255-template
            img_playArea = 255-img_playArea
        #c, w, h = template.shape[::-1]    #for drawing rectangles on frame caps
        method = course[2]
        threshold = course[3]
        res = cv2.matchTemplate(img_playArea, template, method)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
        #print(gamestate.count, min_val, course[0])
        if method == cv2.TM_SQDIFF_NORMED:
            #look for min
            if min_val <= threshold:
                gamestate.currentCourse = course[0]
                gamestate.currentCourseIndex = indexVal
                print(gamestate.count, gamestate.currentCourse)
                break
        else:
            if max_val >= threshold:
                gamestate.currentCourse = course[0]
                gamestate.currentCourseIndex = indexVal
                print(gamestate.count, gamestate.currentCourse)
                break


def findAnItem(image, gamestate):
    img_itemBoxArea = image[72:192, 1167:1323]  #image[30:200, 1100:1400]   #image[72:192, 1167:1323]
    foundItemName = None
    #loop all items
    print(gamestate.count, "Trying to find an item...")
    for i, item in enumerate(items):
        template = item[1]
        method = item[2]
        threshold = item[3]
        #print(item[0])
        res = cv2.matchTemplate(img_itemBoxArea, template, method)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)

        if method == cv2.TM_SQDIFF_NORMED:
            #look for min
            if min_val <= threshold:
                if item[0] != "BlankItem":
                    foundItemName = item[0]
                    print(gamestate.count, foundItemName)
                    gamestate.itemRoulette.append(foundItemName)
                    break  # we should only get one item, stop looking for more items
        else:
            if max_val >= threshold:
                if item[0] != "BlankItem":
                    foundItemName = item[0]
                    print(gamestate.count, foundItemName)
                    gamestate.itemRoulette.append(foundItemName)
                    break  # we should only get one item, stop looking for more items
    if foundItemName is not None:
        gamestate.foundAnItem = True
        print(gamestate.count, "Will now try to find given item")


#Found one occurrence when using a boo 45 seconds after receiving it
#So first find a frame without a boo, then go back and go forwards to find the item given
#  IMPORTANT: If the item is a blank, that means it is blinking and the boo didnt give an item
#       Wwhich is essentially like finding no item, so reset the vars similarly to end of item
#WARNING: If there are two boos in a row from different item boxes, this could skip the item
#    that was given from the first boo
def findBooItem(image, gamestate):
    img_itemBoxArea = image[72:192, 1167:1323]  #image[30:200, 1100:1400]   #image[72:192, 1167:1323]
    foundItemName = None
    #First try to not find a boo
    if gamestate.foundNoBoo == False:
        print(gamestate.count, "Trying to skip ahead and find NO Boo...")
        template = itemsBooFirst[0][1]
        method = itemsBooFirst[0][2]
        threshold = itemsBooFirst[0][3]
        res = cv2.matchTemplate(img_itemBoxArea, template, method)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
        if method == cv2.TM_SQDIFF_NORMED:
            #notice these comparitors are flipped because i dont want to find it!
            if min_val > threshold:
                gamestate.foundNoBoo = True
                print(gamestate.count, "Found NO Boo. Now go back and search forward to find item")
        else:
            if max_val < threshold:
                gamestate.foundNoBoo = True
                print(gamestate.count, "Found NO Boo. Now go back and search forward to find item")
    else:
        #loop all items
        print(gamestate.count, "Trying to find the Boo item...")
        for i, item in enumerate(itemsBooFirst):
            template = item[1]
            method = item[2]
            threshold = item[3]
            #print(item[0])
            res = cv2.matchTemplate(img_itemBoxArea, template, method)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)

            if method == cv2.TM_SQDIFF_NORMED:
                #look for min
                if min_val <= threshold and item[0] != "Boo":
                    foundItemName = item[0]
                    print(gamestate.count, foundItemName)
                    gamestate.itemRoulette.append(foundItemName)
                    break  # we should only get one item, stop looking for more items
            else:
                if max_val >= threshold and item[0] != "Boo":
                    foundItemName = item[0]
                    print(gamestate.count, foundItemName)
                    gamestate.itemRoulette.append(foundItemName)
                    break  # we should only get one item, stop looking for more items
        if foundItemName == "BlankItem":
            print(gamestate.count, "Boo gave no item, reset - Found NO item")
            gamestate.itemRoulette.clear()
            gamestate.foundAnItem = False
            gamestate.foundNoBoo = False
            gamestate.foundGivenItem = False
        elif foundItemName is not None:
            gamestate.foundGivenItem = True
            getPlace(image, gamestate)  #get the current place
            print("Current place is:", gamestate.place)
            tmp = [gamestate.currentCourse, foundItemName, gamestate.place, gamestate.count, videoName]
            with open('./stats/ItemStats.csv','a') as f:
                writer = csv.writer(f)
                writer.writerow(tmp)
            itemStats.append(tmp)
            print("Found given item")
            print(itemStats)
            print(gamestate.count, "Will now try to find NO item")
            #reset vars when we find the given item
            gamestate.itemRoulette.clear()
            gamestate.foundAnItem = False
            gamestate.foundNoBoo = False


#just trying to match blank item here, for efficiency
def findFirstBlankInRoulette(image, gamestate):
    img_itemBoxArea = image[72:192, 1167:1323]  # image[30:200, 1100:1400]
    template = items[gamestate.blankItemIndex][1]
    method = items[gamestate.blankItemIndex][2]
    threshold = items[gamestate.blankItemIndex][3]
    print(gamestate.count, "Trying to find first blank in roulette...")

    res = cv2.matchTemplate(img_itemBoxArea, template, method)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
    #print(gamestate.count, item[0], min_val)
    if method == cv2.TM_SQDIFF_NORMED:
        #look for min
        if min_val <= threshold:
            gamestate.foundBlankItem = True
            foundItemName = items[gamestate.blankItemIndex][0]
            print(gamestate.count, foundItemName)
    else:
        if max_val >= threshold:
            gamestate.foundBlankItem = True
            foundItemName = items[gamestate.blankItemIndex][0]
            print(gamestate.count, foundItemName)



def findGivenItem(image, gamestate):
    img_itemBoxArea = image[72:192, 1167:1323]  # image[30:200, 1100:1400]
    foundItemName = None
    print(gamestate.count, "Trying to find given item...")
    for i, item in enumerate(items):
        template = item[1]
        method = item[2]
        threshold = item[3]

        res = cv2.matchTemplate(img_itemBoxArea, template, method)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
        #print(gamestate.count, item[0], min_val)
        if method == cv2.TM_SQDIFF_NORMED:
            #look for min
            if min_val <= threshold:
                if item[0] != "BlankItem":
                    foundItemName = item[0]
                    print(gamestate.count, foundItemName)
                break  # we should only get one item, stop looking for more items for this frame
        else:
            if max_val >= threshold:
                if item[0] != "BlankItem":
                    foundItemName = item[0]
                    print(gamestate.count, foundItemName)
                break  # we should only get one item, stop looking for more items for this frame
    
    if foundItemName is None:
        return  #do nothing
    else:
        gamestate.foundGivenItem = True
        getPlace(image, gamestate)  #get the current place
        print("Current place is:", gamestate.place)
        tmp = [gamestate.currentCourse, foundItemName, gamestate.place, gamestate.count, videoName]
        with open('./stats/ItemStats.csv','a') as f:
            writer = csv.writer(f)
            writer.writerow(tmp)
        itemStats.append(tmp)
        print("Found given item")
        print(itemStats)
        print(gamestate.count, "Will now try to find NO item")
        gamestate.newItemRoulette = [None, None]  #make sure this is reset!
        #reset vars when we find the given item
        gamestate.itemRoulette.clear()
        gamestate.foundAnItem = False
        gamestate.foundBlankItem = False



def findNoItem(image, gamestate):
    img_itemBoxArea = image[72:192, 1167:1323] #image[30:200, 1100:1400]   #image[72:192, 1167:1323]
    foundItemName = None
    thresholdBuffer = .1
    print(gamestate.count, "Trying to find NO item...")
    #loop all items
    for i, item in enumerate(items):
        template = item[1]
        method = item[2]
        threshold = item[3]

        res = cv2.matchTemplate(img_itemBoxArea, template, method)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)

        if method == cv2.TM_SQDIFF_NORMED:
            #look for min
            if min_val <= threshold + thresholdBuffer:
                foundItemName = item[0]
                if foundItemName != "BlankItem":
                    if gamestate.goToSecondFrame == True:
                        gamestate.newItemRoulette[0] = foundItemName
                    else:
                        gamestate.newItemRoulette[1] = foundItemName
                #gamestate.itemRoulette.append(foundItemName)
                break  # we should only get one item, stop looking for more items
        else:
            if max_val >= threshold - thresholdBuffer:
                foundItemName = item[0]
                if foundItemName != "BlankItem":
                    if gamestate.goToSecondFrame == True:
                        gamestate.newItemRoulette[0] = foundItemName
                    else:
                        gamestate.newItemRoulette[1] = foundItemName
                #gamestate.itemRoulette.append(foundItemName)
                break  # we should only get one item, stop looking for more items
    if foundItemName is None:
        gamestate.foundAnItem = False
        gamestate.foundGivenItem = False
        gamestate.itemRoulette.clear()
        gamestate.newItemRoulette = [None, None]
        gamestate.goToSecondFrame = True
        print(gamestate.count, "Found NO item")



#every 40 frames
def findBlackScreen(image, gamestate):
    img_playArea = image[:, 560:]

    #need to invert the image to do matching well - essentially matching all white screen
    img_playArea = 255-img_playArea
    blackScreenG = 255-blackScreen

    res = cv2.matchTemplate(img_playArea, blackScreenG, cv2.TM_SQDIFF_NORMED)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
    #print(min_val)
    if min_val <= .001:
        print(gamestate.count, "Found Black Screen! Resetting gamestate")

        gamestate.itemRoulette.clear()
        gamestate.currentCourse = ""
        #gamestate.currentCourseIndex = 0
        gamestate.foundAnItem = False
        gamestate.foundNoItem = False
        gamestate.foundBlankItem = False
        gamestate.foundGivenItem = False
        gamestate.inNewItemRoulette = False
        gamestate.place = 8



def localSetup():
    #list of lists of item stats - could be list of tuples, i dont know
    global itemStats 
    itemStats = []  #[['ItemName', course (string), place (int), count (int) - current frame count],...]
    global items, itemsBooFirst, places, courses, masks
    items, places, courses, masks = setup.setup()
    itemsBooFirst = [items[3]] + items[:3] + items[4:]
    global blackScreen 
    blackScreen = cv2.imread("./otherPics/" + 'black.png')

main()
