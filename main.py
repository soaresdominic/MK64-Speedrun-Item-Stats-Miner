'''
Project: MK64 item stats miner
Purpose: to retreive and analyze item box counts / stats during full game skips speedruns
Description:
Loop over all videos in folder and analyze the frames sequentially to determine what items are given
by the item roulette. Collect stats on Place, Item, Course, Frame, Video. Append these stats to a file - 
append these stats so if the program stops working it retains the stats
Assumptions:
 - videos are less than 20 hours
 - input videos are 1080p, same format as current vids as of 8/12/21
 - videos don't start during a run (if no frame range entered)

Requirements:
-python3 64 bit
- ~9 GB RAM Free - close google chrome ;)
-opencv-python (cv2)
-psutil

Usage (preferred):
-Navigate to root folder in powershell
-py main.py

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

Multi-Threading:
-One thread continually populates a list of the next x frames
-As we advance the framenum / count, we remove any frames from the start of the list
    where number removed is the difference between the next frame and frame cutoff value
    e.g. frame cutoff 800 next frame is 920, remove 120 frames from start of list
    list will then keep populating the next 120 free spots at end of the list
-allow skipping this for major skips forward, so we dont remove a frame we need if we need to go backwards
these minus frames are never done more than once at a time, except for one for finding given item (-1 for max 5 frames)

Video Ranges:
A text file "videoRanges.csv" created in the root folder. the text file has the following format
video filename, start minute of video to process, end minute of video to process,  start minute of video to process, end minute of video to process, etc.
minutes are integers and can be 0 or after video ends. put a 1 minute buffer to each time 5,10 -> 4,11

ToDo:
error - same video
starting at 7192
['LuigiRaceway', 'RedShell', 3, 8140, '2021-07-17 17-44-28.mkv'], ['LuigiRaceway', 'Star', 3, 8927, '2021-07-17 17-44-28.mkv'], ['LuigiRaceway', 'Star', 4, 9700, '2021-07-17 17-44-28.mkv'], ['LuigiRaceway', 'Lightning', 4, 10542, '2021-07-17 17-44-28.mkv']
starting at 0
['LuigiRaceway', 'RedShell', 3, 8159, '2021-07-17 17-44-28.mkv'], ['LuigiRaceway', 'Star', 3, 8953, '2021-07-17 17-44-28.mkv'], ['LuigiRaceway', 'Star', 4, 9727, '2021-07-17 17-44-28.mkv'], ['LuigiRaceway', 'Lightning', 4, 10563, '2021-07-17 17-44-28.mkv']
'''

import cv2
import numpy as np
import csv
import setup
import os
import datetime
from threading import Thread
from queue import Queue
import time
import sys
import psutil
import math


class Gamestate:
    '''
    place = 8  #current place in the race
    count = 0  #Frame count of current vid
    
    inNewItemRoulette = False  #when trying to find no item, if newItemRoulette has two different items
    foundBlankItem = False  #found first blank item in roulette

    currentCourseIndex = 0  #current / last course index
    currentCourse = ""   #current course string

    foundAnItem = False  #Found first item signifying we're in a roulette
    foundNoItem = False  #after finding the given item, trying to find no item visible
    foundGivenItem = False  #when we determine the item given
    foundNoBoo = False  #When we are trying to find no boo after getting one
    lastItemBooItem = False  #When the boo gives us an item this is True

    searchingForLuigiRestart = False  #skipping ahead to see if we are back on luigi raceway
    checkStillInCourse = False  #after skipping frames at race start, check we didnt exit out of race for some reason
    checkingOnceForRaceStart = False  #after finding race end, we're checking for the race start of the next race
                                if we just ended on a non resetting course

    goToAdjacentFrame = False  #when trying to see if we're in a new roulette, check frame next to current one
    goToSecondAdjacentFrame = False  #if foundDoubleAfterTriple or foundSingleAfterTriple, we want to check 2 frames after also
    foundTripleAfterTriple = False  #last given item was triple mushrooms, see this item again
    foundDoubleAfterTriple = False  #last given item was triple mushrooms, see double mushrooms
    foundSingleAfterTriple = False  #last given item was triple mushrooms, see single mushroom

    blankItemIndex = i   #index of the blankitem in the items list, get it dynamically
    '''

    def __init__(self):
        self.place = 0
        self.count = 0
        self.lastGivenItem = ""
        
        self.inNewItemRoulette = False
        self.foundBlankItem = False

        self.currentCourseIndex = 0
        self.currentCourse = ""
        self.noItemsToadsTurnpike = False

        self.foundAnItem = False
        self.foundNoItem = False  #only used after we get an item, so default is False
        self.foundGivenItem = False
        self.foundNoBoo = False  #this is true after we get a boo and then find a frame without it
        self.lastItemBooItem = False

        self.searchingForLuigiRestart = False
        self.checkStillInCourse = False
        self.checkingOnceForRaceStart = False

        self.goToAdjacentFrame = False
        self.goToSecondAdjacentFrame = False
        self.foundTripleAfterTriple = False
        self.foundDoubleAfterTriple = False
        self.foundSingleAfterTriple = False
        
        for i, item in enumerate(items):
            if item[0] == "BlankItem":
                self.blankItemIndex = i
                break

    #Reset specific vars after race end / blackscreen that are specific to the race only
    def resetRaceVars(self):
        self.place = 0
        self.lastGivenItem = ""

        self.inNewItemRoulette = False
        self.foundBlankItem = False
        self.currentCourse = ""
        self.noItemsToadsTurnpike = False

        self.foundAnItem = False
        self.foundNoItem = False 
        self.foundGivenItem = False
        self.foundNoBoo = False 
        self.lastItemBooItem = False

        self.goToAdjacentFrame = False
        self.goToSecondAdjacentFrame = False
        self.foundTripleAfterTriple = False
        self.foundDoubleAfterTriple = False
        self.foundSingleAfterTriple = False


class FileVideoStream:
    #1000 frames should be 6GB ish
    def __init__(self, path):
        # initialize the file video stream along with the boolean
        # used to indicate if the thread should be stopped or not
        self.stream = cv2.VideoCapture(path)
        self.Frames = []
        self.stopped = False
        self.removedFrames = 0
        self.xOffset = 560
        self.yOffset = 1020
        self.timeToFull = 0   #seconds requred to buffer all x frames from an empty list
        self.FrameCutoff = 200  #highest is -150 possible for finding boo 
        self.skipRemovingFrames = False  #this is so for skipping ahead a lot (700 frames, i dont need the framecutoff to be huge
        self.CurrentlyRemovingFrames = False  #lock process so new thread cannot add frames while we are currently removing them
        #get how many frames we can reasonbly fit with the amount of memory we have
        #leave 1GB extra
        stats = psutil.virtual_memory()  # returns a named tuple
        available = getattr(stats, 'available')
        self.maxNumFrames = math.floor( (available - 1073741824) / 4406536 )   #4406536 size of one frame
        print("Using", self.maxNumFrames, "Max Frames")

    def start(self, frameNum):
        # start a thread to read frames from the file video stream
        if frameNum != 0:
            self.stream.set(cv2.CAP_PROP_POS_FRAMES, frameNum)   #sets the frame to read
        t = Thread(target=self.update, args=())
        t.daemon = True
        t.start()
        return self

    def update(self):
        # keep looping infinitely
        while True:
            # if the thread indicator variable is set, stop the
            # thread
            if self.stopped:
                return
            # otherwise, ensure the list has room in it
            if self.notFull() and not self.CurrentlyRemovingFrames:
                # read the next frame from the file
                #if i != self.stream.get(cv2.CAP_PROP_POS_FRAMES) - 1:
                #    print("ASDADDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDD")
                #print(self.stream.get(cv2.CAP_PROP_POS_FRAMES), i)
                grabbed, frame = self.stream.read()  
                #print(len(self.Frames))
                # if the `grabbed` boolean is `False`, then we have
                # reached the end of the video file
                if not grabbed:
                    self.stop()
                    return
                # add the frame to the list
                self.Frames.append(frame[:self.yOffset , self.xOffset:].copy())
            #DEBUG
            #elif self.CurrentlyRemovingFrames:
            #    print("WARNING WE MAYBE WOULD HAVE SKIPPED THIS FRAME BEFORE!!!!!!!!!!------------------!!!!!!!!!!!!!!!!!")


    def ResetForNewVideo(self):
        self.Frames.clear()
        print("Deallocating the memory for the old frames...")
        time.sleep(3.0)  #allow some time for the memory to be deallocated
        self.stopped = False
        self.removedFrames = 0
        print("Done. recalculating how much space we have for new video")

    def removeFrames(self, numFrames):
        self.CurrentlyRemovingFrames = True
        #self.Frames = self.Frames[numFrames:]
        del self.Frames[:numFrames]  #This is important, there seemed to have been a bug with the splicing, must delete instead
        self.CurrentlyRemovingFrames = False
        self.removedFrames += numFrames

    def read(self, i):
        # return frame from index i
        while True:
            try:
                #print("Reading Frame", i)
                return True, self.Frames[i]
            except:
                print("HAVENT READ THE REQUESTED FRAME YET FROM THE VIDEO!-----------------------------------------")
                print("waiting until we're back up to", int((self.maxNumFrames * .7 )), "read frames")
                #print("waiting until we're back up to", self.maxNumFrames, "read frames")
                #while self.notFull():
                print("Sleeping", round(self.timeToFull * .7, 2), "seconds")
                time.sleep(round(self.timeToFull * .7, 2))
                while len(self.Frames) < int((self.maxNumFrames * .7 )):   #less than 70% full
                    time.sleep(0.1)
                #print("Done. We can now continue")

    def notFull(self):
        # return True if there are still frames in the queue
        return len(self.Frames) < self.maxNumFrames

    def stop(self):
        # indicate that the thread should be stopped
        self.stopped = True



def main():
    localSetup()  #grab all the pics and things for image matching
    videoRanges = getVideoRanges()  #dictionary of {videofilename: [(range start, range end), (range start, range end), ...], ...}
    print("Video Ranges loaded")
    print(videoRanges)
    if not os.path.isdir("./stats/"):
        os.mkdir("./stats/")
    #will create it if not already present
    if os.path.isfile('./stats/ItemStats.csv'):
        rmethod = 'a'
    else:
        rmethod = 'w'
    with open('./stats/ItemStats.csv',rmethod, newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Starting analysis on all videos - ' + str(datetime.datetime.now())])
        writer.writerow(['Video Ranges loaded:'] + [(k,v) for k,v in videoRanges.items()])
    #For each video we have in the directory of videosToAnalyze
    videosDirectory = './videosToAnalyze/'
    for videoFileName in os.listdir(videosDirectory):
        if videoFileName[len(videoFileName)-3:].lower() not in ["mkv", "mp4", "flv", "mov"]:
            continue
        global videoName
        videoName = videoFileName

        if videoFileName not in videoRanges:
            videoRanges[videoFileName] = [(None, None)]

        for startEndTime in videoRanges[videoFileName]:
            if startEndTime[0] is None and startEndTime[1] is None:
                startFrame = 0
                endFrame = 2157840  #<- lazy programming - 20 hours of 29.97 framerate video
            else:
                if startEndTime[0] < 0:
                    startEndTime[0] = 0
                startFrame = int(startEndTime[0]*29.97*60)
                endFrame = int(startEndTime[1]*29.97*60)
            frameNum = startFrame  #debug 7000 5915 #12749 #32350 #5400 #10141 #5000  #13000

            #Creating the video reading thread and filling the list
            fvs = FileVideoStream(videosDirectory + videoFileName).start(frameNum)
            print("Waiting to buffer all", fvs.maxNumFrames, "frames")
            startTime = time.time()
            while fvs.notFull():
                time.sleep(.25)
            fvs.timeToFull = round(time.time() - startTime, 2)
            print(len(fvs.Frames), "Frames all buffered")

            with open('./stats/ItemStats.csv','a', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['Starting analysis on video: ' + videoName])

            print("Analyzing video " + videoFileName)
            gamestate = Gamestate()
            fvs.removedFrames = frameNum  #incase we started at not 0
            gamestate.count = frameNum

            #Loop to read images from video
            while True:
                fvsIndex = frameNum - fvs.removedFrames
                #print("fvsIndex:", fvsIndex)
                success, image = fvs.read(fvsIndex)
                #vidcap.set(cv2.CAP_PROP_POS_FRAMES, frameNum)   #sets the frame to read
                #success,image = vidcap.read()
                if fvs.stopped:
                    break

                frameNumBeforeChange = frameNum
                #if current course is empty, loop until we find one
                if gamestate.currentCourse == "":
                    skipFrames = findCourse(image, gamestate, fvs, fvsIndex)
                    if gamestate.checkingOnceForRaceStart:
                        gamestate.checkingOnceForRaceStart = False
                        if gamestate.currentCourse == "":
                            frameNum -= 775
                            gamestate.count -= 775
                    if gamestate.currentCourse == "":  #didnt find one, skip 110 frames, below lap time is still for 110
                        if gamestate.searchingForLuigiRestart:
                            #we had skipped 400 frames so if this is false go back 400
                            frameNum -= 400
                            gamestate.count -= 400
                            gamestate.searchingForLuigiRestart = False
                        frameNum += 110
                        gamestate.count += 110
                    else:
                        if gamestate.searchingForLuigiRestart:
                            #print(gamestate.count, "We did restart Luigi Raceway!")
                            gamestate.searchingForLuigiRestart = False
                        if skipFrames != 0:  #if we want to skip frames to first item box
                            print(gamestate.count, "Skipping to right before first item set in course")
                            frameNum += skipFrames
                            gamestate.count += skipFrames
                            gamestate.checkStillInCourse = True
                        continue
                elif gamestate.currentCourse == "FrappeSnowland" or  gamestate.currentCourse == "WarioStadium" or gamestate.noItemsToadsTurnpike:
                    #Skip to just look for black screen, since there will never be items
                    print(gamestate.count, "No items course, searching for black screen...")
                    frameNum += 40  #based on lowest black screen framecount (resets - 40 frames)
                    gamestate.count += 40
                elif gamestate.checkStillInCourse:
                    print(gamestate.count, "Will now check that we're still in this race")
                    #this function will do any variable resetting if we are not in the course anymore
                    checkStillInCourse(image, gamestate)
                #if we're in a course and we have not found an item - try to find an item or a black screen
                elif not gamestate.foundAnItem and not gamestate.foundGivenItem:
                    findAnItem(image, gamestate)
                    if not gamestate.foundAnItem:  #didnt find item
                        frameNum += 25  #based on fastest roulette (on royal raceway)
                        gamestate.count += 25
                    else:
                        continue
                #if we're in a course and we have found an item
                elif gamestate.foundAnItem and not gamestate.foundGivenItem and not gamestate.foundBlankItem:
                    findFirstBlankInRoulette(image, gamestate)
                    if not gamestate.foundBlankItem:  #still havent found the first blank
                        frameNum += 4   #5 frames of blanks so 4 should always hit
                        gamestate.count += 4
                    else:  #found the blank item
                        continue
                #if we're in a course and we have found the blank item, go backwards until we hit the last item
                elif gamestate.foundAnItem and not gamestate.foundGivenItem:
                    findGivenItem(image, gamestate)
                    if not gamestate.foundGivenItem:  #still havent nailed down the given item
                        frameNum -= 1
                        gamestate.count -= 1
                    else:  #found the given item
                        continue
                #if we got a boo, find the item it gives us / try to find no boo, then go backwards then forwards
                elif gamestate.foundGivenItem and gamestate.lastGivenItem == 'Boo' and not gamestate.foundNoBoo:
                    findBooItem(image, gamestate)
                    if not gamestate.foundNoBoo:
                        frameNum += 5*30  #skip ahead five seconds
                        gamestate.count += 5*30
                    else:
                        frameNum -= 5*30  #skip back once
                        gamestate.count -= 5*30
                        continue
                #If we just got a boo, find the item the boo gives you
                #Once we record this next item, this elif will no longer hit
                #THIS SECOND 1 FOR INDEXING IS IMPORTANT IF THE ITEMSTATS LIST IS CHANGED
                elif gamestate.foundGivenItem and gamestate.lastGivenItem == 'Boo' and gamestate.foundNoBoo:
                    findBooItem(image, gamestate)
                    #First check if the boo gave us no item - we want to skip 86 frames if it did
                    #91 frames of time from first frame of first blink to last frame of BOO item on screen
                    #This could be changed - but this makes sure we dont find a boo as a normal item if we
                    #   enter the find item loop too early
                    if not gamestate.foundAnItem and not gamestate.foundGivenItem:
                        frameNum += 91
                        gamestate.count += 91
                    if gamestate.lastGivenItem == 'Boo':
                        frameNum += 5
                        gamestate.count += 5
                    else:  #found the boo item
                        continue
                #if we just determined the given item
                #try to find no item, black screen, or determine if we're in another item roulette
                #If we're in another roulette, cant just look every x frames since the same item could
                #   be the frame we found in the new roulette, but since its the same it wont register as new
                #Do pairs of frames every 20 frames to see if they have different items
                elif gamestate.foundGivenItem:
                    findNoItem(image, gamestate)
                    if not gamestate.foundNoItem:  #still have item in inventory
                        #should be able to do 20 frames, gives enough time if we go into new
                        #roulette for us to realize that between the 20-25th last 5 frames
                        #of the roulette
                        if gamestate.goToAdjacentFrame or gamestate.goToSecondAdjacentFrame:
                            frameNum += 1
                            gamestate.count += 1
                        #we did go to adjacent frame twice, so only skip 18 frames not 19
                        elif gamestate.foundDoubleAfterTriple or gamestate.foundSingleAfterTriple:
                            frameNum += 18
                            gamestate.count += 18
                        else:
                            frameNum += 19
                            gamestate.count += 19
                    else:  #found no item
                        continue

                #Very last thing for EVERY frame inside a course is check for black screen.
                #Reset all vars in function if we find it
                if gamestate.currentCourse != "":
                    findBlackScreen(image, gamestate)
                    #if we didnt find a black screen, current course is still != ""
                    #now search for race finish - non resetting races
                    if gamestate.currentCourse != "":
                        findEndOfRace(image, gamestate)
                        if gamestate.currentCourse == "":  #Found end of race
                            if gamestate.checkingOnceForRaceStart:
                                frameAdvance = courses[gamestate.currentCourseIndex][5]
                                print(gamestate.count, "Checking ahead", frameAdvance, "frames")
                                frameNum += frameAdvance
                                gamestate.count += frameAdvance
                                fvs.skipRemovingFrames = True
                            else:
                                frameNum += 300
                                gamestate.count += 300
                                #wont ever go back on these 300 so no need to skipremovingframes
                    else:  #we did find a black screen
                        #check if we are restarting on luigi raceway
                        if gamestate.currentCourseIndex == 0:
                            #about 400 frames between black screen on restarting luigi raceway and last frame of race start
                            print(gamestate.count, "Checking if we are restarting on Luigi Raceway...")
                            frameNum += 400
                            gamestate.count += 400
                            gamestate.searchingForLuigiRestart = True
                            fvs.skipRemovingFrames = True

                #At the very end of each frame analysis, check if we need to remove frames from list
                #if the next index will be >800, remove the number of frames above 800 we are from the beginning
                #At this point frameNum is pointing to the next frame we want to look at
                if ((frameNum - fvs.removedFrames) > fvs.FrameCutoff) and not fvs.skipRemovingFrames:
                    framesToRemove = (frameNum - fvs.removedFrames) - fvs.FrameCutoff
                    fvs.removeFrames(framesToRemove)
                    #print("Removed ", framesToRemove, "Frames")
                    #other thread should fill up the array to 1000 frames again
                elif fvs.skipRemovingFrames:
                    fvs.skipRemovingFrames = False  #reset this after skipping directly above
                
                if frameNum > endFrame:
                    fvs.stopped = True
            
            #At end of the current time range
            print("End of time range")
            fvs.ResetForNewVideo()

        #At the end of the current vid
        print("Done!")
        with open('./stats/ItemStats.csv','a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['Done with analysis on video: ' + videoName + str(datetime.datetime.now())])
        #important, reset the vars for the frame list and things
        fvs.ResetForNewVideo()
    with open('./stats/ItemStats.csv','a', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Done with analysis on all videos - ' + str(datetime.datetime.now())])



#Although it doesnt seem like it, there is a lot of variance in the color of the places (capture card related?)
#enough to where the darkest 1st has the same color as the brightest 2nd
def getPlace(image, gamestate):
    #First we can rule out 8th, since it's very common, with basic color detection
    image_8th = image[865:879, 728-560:739-560]
    image_8th = cv2.cvtColor(image_8th, cv2.COLOR_BGR2GRAY)
    #print(image_8th)
    if min(min(image_8th, key=min)) >= 90 and max(max(image_8th, key=max)) <= 110:
        gamestate.place = 8
        return

    #Now do matching for other places
    #Masking took a while to figure out, it may not be perfect
    image_place = image[700:980, 600-560:930-560]  #[650:880, 750:930]
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



def findCourse(image, gamestate, fvs, fvsIndex):
    img_playArea = image[135:, :]   #135 is y value that cuts off lap / time
    if gamestate.currentCourseIndex == 0:
        potentialNextCourses = [0,1,4,8,12]
    else:
        if gamestate.currentCourseIndex == 15:
            potentialNextCourses = [0]
        else:
            potentialNextCourses = [0, gamestate.currentCourseIndex + 1]

    print(gamestate.count, "Searching for course...")
    for indexVal in potentialNextCourses:  #for each of the selected potential next courses
        course = courses[indexVal]
        template = course[1]
        #cut top off lap / time because then we can add 30 frames to the window
        template = template[150:, :]
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
            if min_val <= threshold + .01:   #.01 deviation possible
                gamestate.currentCourse = course[0]
                gamestate.currentCourseIndex = indexVal
                print(gamestate.count, gamestate.currentCourse)
                if gamestate.currentCourse == "ToadsTurnpike":
                    print(gamestate.count, "Check if this is new strat toads turnpike with no items or old strat")
                    success, imagepl = fvs.read(fvsIndex + 240)  #8 seconds after, check for 8th place
                    #cv2.imwrite("./test.png", imagepl)
                    getPlace(imagepl, gamestate)  #get the current place
                    if gamestate.place == 8:
                        print(gamestate.count, "NEW strat toads turnpike")
                        gamestate.noItemsToadsTurnpike = True
                    else:
                        print(gamestate.count, "OLD strat toads turnpike")
                return course[4]
        else:
            if max_val >= threshold:
                gamestate.currentCourse = course[0]
                gamestate.currentCourseIndex = indexVal
                print(gamestate.count, gamestate.currentCourse)
                return course[4]


def findAnItem(image, gamestate):
    img_itemBoxArea = image[72:192, 1167-560:1323-560]  #image[30:200, 1100:1400]   #image[72:192, 1167:1323]
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
                    break  # we should only get one item, stop looking for more items
        else:
            if max_val >= threshold:
                if item[0] != "BlankItem":
                    foundItemName = item[0]
                    print(gamestate.count, foundItemName)
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
    img_itemBoxArea = image[72:192, 1167-560:1323-560]  #image[30:200, 1100:1400]   #image[72:192, 1167:1323]
    foundItemName = None
    #First try to not find a boo
    if not gamestate.foundNoBoo:
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
                    break  # we should only get one item, stop looking for more items
            else:
                if max_val >= threshold and item[0] != "Boo":
                    foundItemName = item[0]
                    print(gamestate.count, foundItemName)
                    break  # we should only get one item, stop looking for more items
        if foundItemName == "BlankItem":
            print(gamestate.count, "Boo gave no item, reset - Found NO item")
            gamestate.foundAnItem = False
            gamestate.foundNoBoo = False
            gamestate.foundGivenItem = False
        elif foundItemName is not None:
            gamestate.foundGivenItem = True
            getPlace(image, gamestate)  #get the current place
            print("Current place is:", gamestate.place)
            tmp = [gamestate.currentCourse, foundItemName, gamestate.place, gamestate.count, videoName]
            gamestate.lastGivenItem = foundItemName
            gamestate.lastItemBooItem = True
            with open('./stats/ItemStats.csv','a', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(tmp)
            itemStats.append(tmp)
            print("Found given item")
            print(itemStats[-50:])  #only print last 50 incase there's a ton from multiple videos
            print(gamestate.count, "Will now try to find NO item")
            #reset vars when we find the given item
            gamestate.foundAnItem = False
            gamestate.foundNoBoo = False


#just trying to match blank item here, for efficiency
def findFirstBlankInRoulette(image, gamestate):
    img_itemBoxArea = image[72:192, 1167-560:1323-560]  # image[30:200, 1100:1400]
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
    img_itemBoxArea = image[72:192, 1167-560:1323-560]  # image[30:200, 1100:1400]
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
        gamestate.lastGivenItem = foundItemName
        gamestate.lastItemBooItem = False
        with open('./stats/ItemStats.csv','a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(tmp)
        itemStats.append(tmp)
        print("Found given item")
        print(itemStats)
        print(gamestate.count, "Will now try to find NO item")
        #reset vars when we find the given item
        gamestate.foundAnItem = False
        gamestate.foundBlankItem = False


#First try to find the same item that was given to us (since that'll be the most common)
    #if we do check the adjascent frame
#if we dont find it, check the other items
    #if we find an item we're in a new roulette
#if we dont find one, then we reset
#For after getting triple mushrooms, we check the next 2 adjacent frames
def findNoItem(image, gamestate):
    img_itemBoxArea = image[72:192, 1167-560:1323-560] #image[30:200, 1100:1400]   #image[72:192, 1167:1323]
    foundItemName = None
    thresholdBuffer = .1
    print(gamestate.count, "Trying to find NO item...")
    #First frame - check for same item, then check for mushrooms, then check all other items
    if not gamestate.goToAdjacentFrame and not gamestate.goToSecondAdjacentFrame:
        #first try to find same item - this is obviously going to be the most common
        item = items[itemNames.index(gamestate.lastGivenItem)]
        template = item[1]
        method = item[2]
        threshold = item[3]
        res = cv2.matchTemplate(img_itemBoxArea, template, method)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
        if min_val <= threshold + thresholdBuffer:
            #just in case we just found the same item in a new roulette, check the adjacent frame for a different item
            #For triple mushrooms we do this normally like every other item, just when we're back in here,
            #   we check for the item to not be triple or double mushroom
            gamestate.goToAdjacentFrame = True
            if item[0] == "TripleMushrooms" and gamestate.lastGivenItem == "TripleMushrooms":
                gamestate.foundTripleAfterTriple = True
                #print("Found Triple After Triple")
            return
        #If the last item given was triple mushrooms, on first frame check for double or single mushroom
        elif gamestate.lastGivenItem == "TripleMushrooms":
            item = items[itemNames.index("DoubleMushrooms")]
            template = item[1]
            method = item[2]
            threshold = item[3]
            res = cv2.matchTemplate(img_itemBoxArea, template, method)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
            if min_val <= threshold + thresholdBuffer:
                gamestate.foundDoubleAfterTriple = True
                #print("Found Double After Triple")
                gamestate.goToAdjacentFrame = True
                return
            else:
                item = items[itemNames.index("Mushroom")]
                template = item[1]
                method = item[2]
                threshold = item[3]
                res = cv2.matchTemplate(img_itemBoxArea, template, method)
                min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
                if min_val <= threshold + thresholdBuffer:
                    gamestate.foundSingleAfterTriple = True
                    #print("Found Single After Triple")
                    gamestate.goToAdjacentFrame = True
                    return
    #if same item was found or double or single after triple mushrooms was found
    elif gamestate.goToAdjacentFrame:
        #Odds are we're gonna see the same item, so do similar above and search for given item first
        item = items[itemNames.index(gamestate.lastGivenItem)]
        template = item[1]
        method = item[2]
        threshold = item[3]
        res = cv2.matchTemplate(img_itemBoxArea, template, method)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
        if min_val <= threshold + thresholdBuffer:
            gamestate.goToAdjacentFrame = False
            gamestate.goToSecondAdjacentFrame = False
            return
        elif gamestate.foundSingleAfterTriple:
            item = items[itemNames.index("Mushroom")]
            template = item[1]
            method = item[2]
            threshold = item[3]
            res = cv2.matchTemplate(img_itemBoxArea, template, method)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
            if min_val <= threshold + thresholdBuffer:
                gamestate.goToAdjacentFrame = False
                gamestate.goToSecondAdjacentFrame = False
                return
            else:
                #check for double then triple
                item = items[itemNames.index("DoubleMushrooms")]
                template = item[1]
                method = item[2]
                threshold = item[3]
                res = cv2.matchTemplate(img_itemBoxArea, template, method)
                min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
                if min_val <= threshold + thresholdBuffer:
                    gamestate.goToAdjacentFrame = False
                    gamestate.goToSecondAdjacentFrame = True
                    return
        elif gamestate.foundDoubleAfterTriple:
            #first check for double again, if it is double, we're not in new roulette, continue as normal
            item = items[itemNames.index("DoubleMushrooms")]
            template = item[1]
            method = item[2]
            threshold = item[3]
            res = cv2.matchTemplate(img_itemBoxArea, template, method)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
            if min_val <= threshold + thresholdBuffer:
                gamestate.goToAdjacentFrame = False
                gamestate.goToSecondAdjacentFrame = False
                return
            else:
                #If we see triple mushrooms we're not sure if we're in a new roulette yet, go to second adjacent
                item = items[itemNames.index("TripleMushrooms")]
                template = item[1]
                method = item[2]
                threshold = item[3]
                res = cv2.matchTemplate(img_itemBoxArea, template, method)
                min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
                if min_val <= threshold + thresholdBuffer:
                    gamestate.goToAdjacentFrame = False
                    gamestate.goToSecondAdjacentFrame = True
                    return
        elif gamestate.foundTripleAfterTriple:
            #check for not double or triple mushroom in second frame
            for i, item in enumerate(items):
                template = item[1]
                method = item[2]
                threshold = item[3]
                res = cv2.matchTemplate(img_itemBoxArea, template, method)
                min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
                #look for min
                if min_val <= threshold + thresholdBuffer:
                    foundItemName = item[0]
                    if foundItemName != "BlankItem" and foundItemName != "TripleMushrooms" and foundItemName != "DoubleMushrooms":
                        #found different item, we must be in a new roulette!
                        gamestate.foundAnItem = True
                        gamestate.foundGivenItem = False
                        print(gamestate.count, "Found a different item! Back into item roulette")
                    #if we found one of those three above, thats normal, just go to next set of frames
                    gamestate.goToAdjacentFrame = False
                    return
    elif gamestate.goToSecondAdjacentFrame:
        #We're only in here if last given item was triple mushrooms and we found single or double in adjacent frame
        if gamestate.foundSingleAfterTriple:
            item = items[itemNames.index("TripleMushrooms")]
            template = item[1]
            method = item[2]
            threshold = item[3]
            res = cv2.matchTemplate(img_itemBoxArea, template, method)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
            if min_val <= threshold + thresholdBuffer:
                #found double then triple after single mushroom, must be in new roulette
                gamestate.foundAnItem = True
                gamestate.foundGivenItem = False
                print(gamestate.count, "Found a different item! Back into item roulette")
                gamestate.goToAdjacentFrame = False
                gamestate.goToSecondAdjacentFrame = False
                return
        elif gamestate.foundDoubleAfterTriple:
            item = items[itemNames.index("DoubleMushrooms")]
            template = item[1]
            method = item[2]
            threshold = item[3]
            res = cv2.matchTemplate(img_itemBoxArea, template, method)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
            if min_val <= threshold + thresholdBuffer:
                gamestate.goToAdjacentFrame = False
                gamestate.goToSecondAdjacentFrame = False
                return
            else:
                #If we see triple mushrooms we're not sure if we're in a new roulette yet, go to second adjacent
                item = items[itemNames.index("TripleMushrooms")]
                template = item[1]
                method = item[2]
                threshold = item[3]
                res = cv2.matchTemplate(img_itemBoxArea, template, method)
                min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
                if min_val <= threshold + thresholdBuffer:
                    gamestate.goToAdjacentFrame = False
                    gamestate.goToSecondAdjacentFrame = False
                    return
    #Now that we are down there, we already checked for the certain items for mushrooms that are the special cases
    #   if we didnt already exit out on a return statement above, now just check for every item
    #   if we find an item that is different than a blank or the last item given that means we must be in
    #   a new roulette
    for i, item in enumerate(items):
        template = item[1]
        method = item[2]
        threshold = item[3]
        res = cv2.matchTemplate(img_itemBoxArea, template, method)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
        #look for min
        if min_val <= threshold + thresholdBuffer:
            foundItemName = item[0]
            if foundItemName != "BlankItem" and gamestate.lastGivenItem != foundItemName:
                #There's a couple case where we're not actually in a new roulette
                if gamestate.foundSingleAfterTriple and gamestate.goToSecondAdjacentFrame and \
                    (foundItemName == "DoubleMushrooms" or foundItemName == "Mushroom"):
                    pass
                elif itemStats[-2][1] == "Boo" and gamestate.lastItemBooItem:
                    #boo items dont mean we're in a new roulette, it is a given item
                    pass
                else:
                    #found different item, we must be in a new roulette!
                    gamestate.foundAnItem = True
                    gamestate.foundGivenItem = False
                    print(gamestate.count, "Found", foundItemName)
                    print(gamestate.count, "Found a different item! Back into item roulette")
            gamestate.goToAdjacentFrame = False
            gamestate.goToSecondAdjacentFrame = False
            return
    
    #If we got through all that without finding anything, we truly have found no item, reset gamestate
    if foundItemName is None:
        gamestate.foundAnItem = False
        gamestate.foundGivenItem = False
        gamestate.goToAdjacentFrame = False
        gamestate.goToSecondAdjacentFrame = False
        print(gamestate.count, "Found NO item")



def findBlackScreen(image, gamestate):
    img_playArea = image[:, :]

    #need to invert the image to do matching well - essentially matching all white screen
    img_playArea = 255-img_playArea
    blackScreenG = 255-blackScreen

    res = cv2.matchTemplate(img_playArea, blackScreenG, cv2.TM_SQDIFF_NORMED)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
    #print(min_val)
    if min_val <= .001:
        print(gamestate.count, "Found Black Screen! Resetting gamestate")
        gamestate.resetRaceVars()


#Like finding a black screen, so do similar var resets
def findEndOfRace(image, gamestate):
    img_total = image[270:345, 1380-560:1530-560]
    res = cv2.matchTemplate(img_total, total_pic, cv2.TM_SQDIFF_NORMED)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
    #print(min_val)
    if min_val <= .01:   #average is .005
        if gamestate.currentCourseIndex in [3,7,11]:  #If we're on a resetting course
            #This should never happen though, since its always blackscreen on resetting courses
            print(gamestate.count, "Found end of race! We're on a resetting race, continue as normal")
        else:
            print(gamestate.count, "Found end of race! We're on a non-resetting race, check for next course race start")
            gamestate.checkingOnceForRaceStart = True
        gamestate.resetRaceVars()


#Like finding a black screen, so do similar var resets
def checkStillInCourse(image, gamestate):
    img_time = image[70:135, 1385-560:1520-560]
    res = cv2.matchTemplate(img_time, time_pic, cv2.TM_SQDIFF_NORMED)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
    #print(min_val)
    #This comparison is the opposite becuase we dont want to find this
    if min_val > .02:
        print(gamestate.count, "Between start of race and frame skip to first item box set, we quit out of the race. Resetting gamestate")
        gamestate.resetRaceVars()
    else:
        print(gamestate.count, "Still in course, continue as normal")
    #did the checking, reset this
    gamestate.checkStillInCourse = False



def localSetup():
    #list of lists of item stats - could be list of tuples, i dont know
    global itemStats 
    itemStats = []  #[['ItemName', course (string), place (int), count (int) - current frame count],...]
    global items, itemsBooFirst, places, courses, masks, itemNames
    items, places, courses, masks, itemNames = setup.setup()
    itemsBooFirst = [items[12]] + items[:12] + items[13:]
    global blackScreen 
    blackScreen = cv2.imread("./otherPics/" + 'black.png')
    global total_pic
    total_pic = cv2.imread("./otherPics/" + 'total.png')
    global time_pic
    time_pic = cv2.imread("./otherPics/" + 'time.png')

def getVideoRanges():
    #Debug
    '''
    cap = cv2.VideoCapture('./videosToAnalyze/2021-07-17 17-44-28.mkv')
    cap.set(cv2.CAP_PROP_POS_FRAMES, (49 + 26/60)*29.97*60) 
    success, r = cap.read()
    cv2.imwrite("./test.png", r)
    exit()
    '''
    data = []
    try:
        with open('videoRanges.csv', newline='') as f:
            reader = csv.reader(f)
            data = list(reader)
    except:
        pass
    videoRanges = {}
    for line in data:
        for i in range(1, len(line), 2):
            if i+1 <= len(line[1:]):
                if line[0] in videoRanges:
                    tmp = videoRanges[line[0]]
                    tmp.append((int(line[i]), int(line[i+1])))
                    videoRanges[line[0]] = tmp
                else:
                    videoRanges[line[0]] = [(int(line[i]), int(line[i+1]))]
            else:
                raise ValueError('Video Ranges must be in format: filename, start minute (integer) to process, end minute to process. in pairs of two.')
    return videoRanges


main()
