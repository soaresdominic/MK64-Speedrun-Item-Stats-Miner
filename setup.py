#A lot of the comments are currently wrong

import cv2

#This could all be read from file... but not doing that right now
#cropped and full items interchangeable, with tweaked thresholds and things 
def setup():
    #no double mushroom because you cant get that from an item box - but maybe it should be added so theres no break in the roulette
    itemsFolderPath = "./items/"
    Banana = cv2.imread(itemsFolderPath + 'Banana.png')  #.7858 max on item, .64 max on other frames TM_CCORR_NORMED
    #Banana = cv2.imread(itemsFolderPath + 'Banana_crop.png')
    BlankItem = cv2.imread(itemsFolderPath + 'BlankItem.png')  #.77, .52 TM_CCORR_NORMED; .74, .42 TM_CCOEFF_NORMED
    BlueShell = cv2.imread(itemsFolderPath + 'BlueShell.png')  #.748 max TM_CCORR_NORMED; .435,  
    #BlueShell = cv2.imread(itemsFolderPath + 'BlueShell_crop.png')
    Boo = cv2.imread(itemsFolderPath + 'Boo.png')  #.666, .64 TM_CCORR_NORMED; .347, .42 TM_SQDIFF_NORMED
    #Boo = cv2.imread(itemsFolderPath + 'Boo_crop.png')
    FakeItemBox = cv2.imread(itemsFolderPath + 'FakeItemBox.png')  #. max TM_CCORR_NORMED
    GoldenMushroom = cv2.imread(itemsFolderPath + 'GoldenMushroom.png')  #. max TM_CCORR_NORMED
    GreenShell = cv2.imread(itemsFolderPath + 'GreenShell.png')  #. max TM_CCORR_NORMED
    #GreenShell = cv2.imread(itemsFolderPath + 'GreenShell_crop.png')  #. max TM_CCORR_NORMED
    Lightning = cv2.imread(itemsFolderPath + 'Lightning.png')  #. max TM_CCORR_NORMED
    #Lightning = cv2.imread(itemsFolderPath + 'Lightning_crop.png')  #. max TM_CCORR_NORMED
    Mushroom = cv2.imread(itemsFolderPath + 'Mushroom.png')  #. max TM_CCORR_NORMED
    #Mushroom = cv2.imread(itemsFolderPath + 'Mushroom_crop.png')  #. max TM_CCORR_NORMED
    QuadBananas = cv2.imread(itemsFolderPath + 'QuadBananas.png')  #. max TM_CCORR_NORMED
    #QuadBananas = cv2.imread(itemsFolderPath + 'QuadBananas_crop.png')  #. max TM_CCORR_NORMED
    RedShell = cv2.imread(itemsFolderPath + 'RedShell.png')  #. max TM_CCORR_NORMED
    #RedShell = cv2.imread(itemsFolderPath + 'RedShell_crop.png')  #. max TM_CCORR_NORMED
    Star = cv2.imread(itemsFolderPath + 'Star.png')  #. max TM_CCORR_NORMED
    #Star = cv2.imread(itemsFolderPath + 'Star_crop.png')
    TripleGreenShells = cv2.imread(itemsFolderPath + 'TripleGreenShells.png')  #. max TM_CCORR_NORMED
    DoubleMushrooms = cv2.imread(itemsFolderPath + 'DoubleMushrooms.png')
    TripleMushrooms = cv2.imread(itemsFolderPath + 'TripleMushrooms.png')  #.83 max TM_CCORR_NORMED
    TripleRedShells = cv2.imread(itemsFolderPath + 'TripleRedShells.png')  #. max TM_CCORR_NORMED

    #create list so we can iterate through all of them
    #structure: list of tuples [(itemname, item, method, threshold value), ...]
    global items
    items = []
    #Order of most likely to be given (usually in 1st or 8th)
    #thresholds based on highest for any item - .011
    #probabilities in comments in order of 1st to 8th
    items.append(("Banana", Banana, cv2.TM_SQDIFF_NORMED, .02))   #30%
    items.append(("GreenShell", GreenShell, cv2.TM_SQDIFF_NORMED, .02))  #30%	5%
    items.append(("Star", Star, cv2.TM_SQDIFF_NORMED, .02))  #  5%	10%	15%	15%	20%	30%	30%
    items.append(("Lightning", Lightning, cv2.TM_SQDIFF_NORMED, .02))   #	5%	5%	10%	10%	15%	20%	20%
    items.append(("TripleRedShells", TripleRedShells, cv2.TM_SQDIFF_NORMED, .02))  #	20%	20%	20%	20%	20%	20%	20%
    items.append(("BlueShell", BlueShell, cv2.TM_SQDIFF_NORMED, .02))  #                		5%	5%	10%	10%	15%
    items.append(("TripleMushrooms", TripleMushrooms, cv2.TM_SQDIFF_NORMED, .02))  #    15%	20%	20%	25%	25%	10%	5%
    items.append(("GoldenMushroom", GoldenMushroom, cv2.TM_SQDIFF_NORMED, .02))  #  5%	10%	10%	10%	10%	10%	10%
    items.append(("RedShell", RedShell, cv2.TM_SQDIFF_NORMED, .02))    #5%	15%	20%	15%	10%	
    items.append(("FakeItemBox", FakeItemBox, cv2.TM_SQDIFF_NORMED, .02))  #10%	5%
    items.append(("Mushroom", Mushroom, cv2.TM_SQDIFF_NORMED, .02))  #10%	5%	5%	5%	5%	
    items.append(("TripleGreenShells", TripleGreenShells, cv2.TM_SQDIFF_NORMED, .02))  #5%	10%	10%	
    items.append(("Boo", Boo, cv2.TM_SQDIFF_NORMED, .02))   #5%  5%
    items.append(("QuadBananas", QuadBananas, cv2.TM_SQDIFF_NORMED, .02))  #5%  5%
    items.append(("BlankItem", BlankItem, cv2.TM_SQDIFF_NORMED, .02)) 
    items.append(("DoubleMushrooms", DoubleMushrooms, cv2.TM_SQDIFF_NORMED, .02)) 

    global itemNames
    itemNames = [x for y in items for x in y if type(x) == str]

    '''
    #order they appear in clip in game
    items.append(("BlankItem", BlankItem, cv2.TM_CCOEFF_NORMED, .7))  #0.748638749 0.616675496
    items.append(("Banana", Banana, cv2.TM_CCOEFF_NORMED, .8))  #0.91917944 0.590928912
    items.append(("QuadBananas", QuadBananas, cv2.TM_CCOEFF_NORMED, .78))  #0.832661331 0.608544469
    items.append(("GreenShell", GreenShell, cv2.TM_CCOEFF_NORMED, .84))  #0.870366812 0.771629572
    items.append(("TripleGreenShells", TripleGreenShells, cv2.TM_CCOEFF_NORMED, .645))  #0.669585705 0.628238797
    items.append(("RedShell", RedShell, cv2.TM_CCOEFF_NORMED, .82))  #0.870431781 0.759965718
    items.append(("TripleRedShells", TripleRedShells, cv2.TM_CCOEFF_NORMED, .67))  #0.715978503 0.627653062
    items.append(("BlueShell", BlueShell, cv2.TM_CCOEFF_NORMED, .67))  #0.72854954 0.592153788
    items.append(("Lightning", Lightning, cv2.TM_CCOEFF_NORMED, .85))  #0.910152614 0.544527948
    items.append(("FakeItemBox", FakeItemBox, cv2.TM_CCORR_NORMED, .75))  #0.826200962 0.800046325  - the last to look for, else x and > .75
    items.append(("Star", Star, cv2.TM_CCOEFF_NORMED, .80))  #0.846419454 0.658237815
    items.append(("Boo", Boo, cv2.TM_CCOEFF_NORMED, .80))  #0.841647148 0.639753699
    items.append(("Mushroom", Mushroom, cv2.TM_CCOEFF_NORMED, .67))  #0.716526031 0.580160439
    items.append(("TripleMushrooms", TripleMushrooms, cv2.TM_CCOEFF_NORMED, .57))  #0.60136497 0.531142533
    items.append(("GoldenMushroom", GoldenMushroom, cv2.TM_SQDIFF_NORMED, .32))  #min threshold, 0.287993759 0.456957668
    '''
    '''
    #Alphabetical
    items.append(("BlankItem", BlankItem, cv2.TM_CCORR_NORMED, .77))
    items.append(("BlueShell", BlueShell, cv2.TM_CCORR_NORMED, .75))
    items.append(("Boo", Boo, cv2.TM_CCORR_NORMED, .75))
    items.append(("FakeItemBox", FakeItemBox, cv2.TM_CCORR_NORMED, .75))
    items.append(("GoldenMushroom", GoldenMushroom, cv2.TM_CCORR_NORMED, .75))
    items.append(("GreenShell", GreenShell, cv2.TM_CCORR_NORMED, .75))
    items.append(("Lightning", Lightning, cv2.TM_CCORR_NORMED, .75))
    items.append(("Mushroom", Mushroom, cv2.TM_CCORR_NORMED, .75))
    items.append(("RedShell", RedShell, cv2.TM_CCORR_NORMED, .75))
    items.append(("Star", Star, cv2.TM_CCORR_NORMED, .75))
    items.append(("TripleGreenShells", TripleGreenShells, cv2.TM_CCORR_NORMED, .75))
    items.append(("TripleMushrooms", TripleMushrooms, cv2.TM_CCORR_NORMED, .83))
    items.append(("TripleRedShells", TripleRedShells, cv2.TM_CCORR_NORMED, .75))
    '''
    #alphabetical
    #items = sorted(items)

    placesFolderPath = "./places/"
    Place_1st = cv2.imread(placesFolderPath + '1st_black.png')
    Place_2nd = cv2.imread(placesFolderPath + '2nd_black.png')
    Place_3rd = cv2.imread(placesFolderPath + '3rd_black.png')
    Place_4th = cv2.imread(placesFolderPath + '4th_black.png')
    Place_5th = cv2.imread(placesFolderPath + '5th_black.png')
    Place_6th = cv2.imread(placesFolderPath + '6th_black.png')
    Place_7th = cv2.imread(placesFolderPath + '7th_black.png')
    Place_8th = cv2.imread(placesFolderPath + '8th_black.png')

    global places
    places = []
    
    places.append(("Place_1st", Place_1st, cv2.TM_CCORR_NORMED))
    places.append(("Place_2nd", Place_2nd, cv2.TM_CCORR_NORMED))
    places.append(("Place_3rd", Place_3rd, cv2.TM_CCORR_NORMED))
    places.append(("Place_4th", Place_4th, cv2.TM_CCORR_NORMED))
    places.append(("Place_5th", Place_5th, cv2.TM_CCORR_NORMED))
    places.append(("Place_6th", Place_6th, cv2.TM_CCORR_NORMED))
    places.append(("Place_7th", Place_7th, cv2.TM_CCORR_NORMED))
    places.append(("Place_8th", Place_8th, cv2.TM_CCORR_NORMED))
    '''
    places.append(("Place_1st", Place_1st, cv2.TM_SQDIFF))
    places.append(("Place_2nd", Place_2nd, cv2.TM_SQDIFF))
    places.append(("Place_3rd", Place_3rd, cv2.TM_SQDIFF))
    places.append(("Place_4th", Place_4th, cv2.TM_SQDIFF))
    places.append(("Place_5th", Place_5th, cv2.TM_SQDIFF))
    places.append(("Place_6th", Place_6th, cv2.TM_SQDIFF))
    places.append(("Place_7th", Place_7th, cv2.TM_SQDIFF))
    places.append(("Place_8th", Place_8th, cv2.TM_SQDIFF))
    '''

    mask_1st = cv2.imread(placesFolderPath + '1st_mask.png')
    mask_2nd = cv2.imread(placesFolderPath + '2nd_mask.png')
    mask_3rd = cv2.imread(placesFolderPath + '3rd_mask.png')
    mask_4th = cv2.imread(placesFolderPath + '4th_mask.png')
    mask_5th = cv2.imread(placesFolderPath + '5th_mask.png')
    mask_6th = cv2.imread(placesFolderPath + '6th_mask.png')
    mask_7th = cv2.imread(placesFolderPath + '7th_mask.png')
    mask_8th = cv2.imread(placesFolderPath + '8th_mask.png')

    global masks
    masks = []
    masks.append(mask_1st)
    masks.append(mask_2nd)
    masks.append(mask_3rd)
    masks.append(mask_4th)
    masks.append(mask_5th)
    masks.append(mask_6th)
    masks.append(mask_7th)
    masks.append(mask_8th)
    

    coursesFolderPath = "./courses/"
    Course_LuigiRaceway = cv2.imread(coursesFolderPath + 'LuigiRaceway.png')
    Course_MooMooFarm = cv2.imread(coursesFolderPath + 'MooMooFarm.png')
    Course_KoopaTroopaBeach = cv2.imread(coursesFolderPath + 'KoopaTroopaBeach.png')
    Course_KalimariDesert = cv2.imread(coursesFolderPath + 'KalimariDesert.png')
    Course_ToadsTurnpike = cv2.imread(coursesFolderPath + 'ToadsTurnpike.png')
    Course_FrappeSnowland = cv2.imread(coursesFolderPath + 'FrappeSnowland.png')
    Course_ChocoMountain = cv2.imread(coursesFolderPath + 'ChocoMountain.png')
    Course_MarioRaceway = cv2.imread(coursesFolderPath + 'MarioRaceway.png')
    Course_WarioStadium = cv2.imread(coursesFolderPath + 'WarioStadium.png')
    Course_SherbetLand = cv2.imread(coursesFolderPath + 'SherbetLand.png')
    Course_RoyalRaceway = cv2.imread(coursesFolderPath + 'RoyalRaceway.png')
    Course_BowsersCastle = cv2.imread(coursesFolderPath + 'BowsersCastle.png')
    Course_DKJungleParkway = cv2.imread(coursesFolderPath + 'DKJungleParkway.png')
    Course_YoshiValley = cv2.imread(coursesFolderPath + 'YoshiValley.png')
    Course_BansheeBoardwalk = cv2.imread(coursesFolderPath + 'BansheeBoardwalk.png')
    Course_RainbowRoad = cv2.imread(coursesFolderPath + 'RainbowRoad.png')

    global courses
    courses = []
    #course order in game / speedruns
    #Name, Image, Match Method, Threshold, # of frames from start of race before its possible to pickup an item (-1 second),
        # of frames between finish (total on screen) and start of next race
    courses.append(("LuigiRaceway", Course_LuigiRaceway, cv2.TM_SQDIFF_NORMED, .03, 150, 750))
    courses.append(("MooMooFarm", Course_MooMooFarm, cv2.TM_SQDIFF_NORMED, .03, 80, 750))
    courses.append(("KoopaTroopaBeach", Course_KoopaTroopaBeach, cv2.TM_SQDIFF_NORMED, .03, 330, 750))
    courses.append(("KalimariDesert", Course_KalimariDesert, cv2.TM_SQDIFF_NORMED, .03, 155, 0))
    courses.append(("ToadsTurnpike", Course_ToadsTurnpike, cv2.TM_SQDIFF_NORMED, .03, 330,710))
    courses.append(("FrappeSnowland", Course_FrappeSnowland, cv2.TM_SQDIFF_NORMED, .03, 0, 710))
    courses.append(("ChocoMountain", Course_ChocoMountain, cv2.TM_SQDIFF_NORMED, .03, 90, 710))
    courses.append(("MarioRaceway", Course_MarioRaceway, cv2.TM_SQDIFF_NORMED, .03, 30, 0))
    courses.append(("WarioStadium", Course_WarioStadium, cv2.TM_SQDIFF_NORMED, .03, 0, 690))
    courses.append(("SherbetLand", Course_SherbetLand, cv2.TM_SQDIFF_NORMED, .03, 90, 740))
    courses.append(("RoyalRaceway", Course_RoyalRaceway, cv2.TM_SQDIFF_NORMED, .03, 120, 750))
    courses.append(("BowsersCastle", Course_BowsersCastle, cv2.TM_SQDIFF_NORMED, .03, 90, 0))
    courses.append(("DKJungleParkway", Course_DKJungleParkway, cv2.TM_SQDIFF_NORMED, .03, 240, 800))
    courses.append(("YoshiValley", Course_YoshiValley, cv2.TM_SQDIFF_NORMED, .03, 90, 700))
    courses.append(("BansheeBoardwalk", Course_BansheeBoardwalk, cv2.TM_SQDIFF_NORMED, .03, 150, 730))
    courses.append(("RainbowRoad", Course_RainbowRoad, cv2.TM_SQDIFF_NORMED, .03, 180, 0))
    '''
    assumptions:
     - dont take the first item set in Koopa Troopa Beach
     - account for old toads turnpike shortcut and getting items there
     - royal raceway based on old shortcut which gets to items faster
    '''

    return items, places, courses, masks, itemNames

