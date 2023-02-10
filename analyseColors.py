################################################################
#
#   INTRO
#
################################################################
# https://stackoverflow.com/questions/3241929/python-find-dominant-most-common-color-in-an-image
# https://charlesleifer.com/blog/using-python-and-k-means-to-find-the-dominant-colors-in-images/
# https://stackoverflow.com/questions/8915113/sort-hex-colors-to-match-rainbow

################################################################
#
#   INCLUDES / REQUIRES
#
################################################################
#import pymongo
from PIL import Image, ImageDraw, ImageColor
import requests
import numpy as np
import math

import binascii
import struct

import scipy
import scipy.misc
import scipy.cluster

import colorsys
import time
import os

#import imgkit


################################################################
#
#   CONFIG
#
################################################################
testImage           = "https://iso.500px.com/wp-content/uploads/2014/07/20485.jpg"
testUrl             = "https://www.duckstudio.design"
testUrl             = "https://www.airbnb.be"

screenshot_delay    = 5

NUM_CLUSTERS        = 10

testUrls = [
    "https://www.d-artagnan.be/",
    "https://duvalbranding.com/",
    "https://www.spotify.com/nl/",
    "https://addemar.com",
    "https://dropsolid.com/nl/",
    "https://www.spotify.com/nl/",
    "https://twitter.com"
    ]


resize_x            = 1500
resize_y            = 1500

swaps_x             = 1000
swaps_y             = 400
swaps_filename      = "_" + str(NUM_CLUSTERS) + "_swaps.png"

hsv_threshold_white = 0.075
hsv_threshold_black = 0.005

################################################################
#
#   INITZ
#
################################################################
#test :
#testUrl = testImage



################################################################
#
#   FUNCTIONS
#
################################################################

##########################################################
#
#   App functions
#
##########################################################
def handleUrl(url):
    print("analysing ", url[0])
    res = analyseUrl(url[0])
    print("res = ", res)

    print(res)
    saveSwapToDb(url[0], res)
    time.sleep(screenshot_delay)


def analyseTest():
    url = testUrls[0]
    print("testing ", url)
    handleUrl(testUrls) 


def analyseUrl(url):
    # first convert url to image
    print(" ")
    print("fetching url and converting to image...")
    print(url)

    imageFile = urlToImg(url)
    print("screenshot saved to: ")
    print(imageFile)
    
    # analyse image
    print("analysing colors...")
    colorsCount = analyseImage(imageFile)
    print(colorsCount)

    # creating color swaps
    res = createColorSwaps(colorsCount, imageFile)

    # kleur zoeken dat meest aanwezig is
    mosts = mostHsvs(colorsCount)
    print("most = ", mosts)

    returnresul = (res, mosts)
    return returnresul

def analyseImage(img):
    # https://stackoverflow.com/questions/3241929/python-find-dominant-most-common-color-in-an-image
    import math
    
    #print('reading image')
    im = Image.open(img)
    im = im.resize((resize_x, resize_y))        # optional, to reduce time
    ar = np.asarray(im)             # convert input to array

    shape = ar.shape
    ar = ar.reshape(np.product(shape[:2]), shape[2]).astype(float)

    #print('finding clusters')
    codes, dist = scipy.cluster.vq.kmeans(ar, NUM_CLUSTERS)
    #print('cluster centres:\n', codes)

    vecs, dist = scipy.cluster.vq.vq(ar, codes)         # assign codes
    counts, bins = np.histogram(vecs, len(codes))       # count occurrences

    # build result : tuple van hexcolor en count
    res = []
    i = 0
    for c in codes:
        res.append(("#" + convertToHex(convertToRgb(c)), convertToRgb(c), counts[i]))
        i = i +1
    
    # result sorteren: sorten op kleur ?
    #res.sort(key=lambda x: x[0], reverse=1)
    res.sort(key=getHsv, reverse=1)
    res.sort(key=getHsvForSort, reverse=1)
    
    return res


def createColorSwaps(colors, filename):
    # config
    size = 2000
    filenameSwaps = filename + swaps_filename

    # init
    imgSwaps = Image.new(mode = "RGBA", size = (swaps_x, swaps_y), color = 'black')
    drawSwaps = ImageDraw.Draw(imgSwaps)

    current_x = 0
    for color in colors:
        # computing sizes
        width = swaps_x * color[2] / resize_x / resize_y
        #width = swaps_x / len(colors)
        x2 = current_x + width
        #print(width)
        #print(round(current_x), round(x2), color[0])

        # drawing rectangle
        drawSwaps.rectangle((current_x, 0, x2, swaps_y), fill=color[0])

        #updating 
        current_x = x2

    imgSwaps.save(filenameSwaps)
    return filenameSwaps


# def readImageFromWeb(url):
#     im = Image.open(requests.get(url, stream=True).raw)
#     return im



##########################################################
#
#   Url functions
#
##########################################################
def urlToImg(url):
    from selenium import webdriver

    filename = urlToFilename(url)

    print(os.name)


    driver = webdriver.PhantomJS()
    driver.set_window_size(500, 450, windowHandle='current')

    print("loading url")
    driver.get(url)
    print("url loaded")
    time.sleep(screenshot_delay)
    print("taking screenshot after %1s", screenshot_delay)
    screenshot = driver.save_screenshot(filename)
    print("screenshot taken")
    #print(screenshot)
    driver.quit()
    return filename


def canonical_url(u):
    from w3lib.url import url_query_cleaner
    from url_normalize import url_normalize

    u = url_normalize(u)
    u = url_query_cleaner(u,parameterlist = ['utm_source','utm_medium','utm_campaign','utm_term','utm_content'],remove=True)

    if u.startswith("http://"):
        u = u[7:]
    if u.startswith("https://"):
        u = u[8:]
    if u.startswith("www."):
        u = u[4:]
    if u.endswith("/"):
        u = u[:-1]

    u = u.replace("/", "")
    return u


def urlToFilename(url):
    return canonical_url(url) + "_" + ".png"



##########################################################
#
#   Color functions
#
##########################################################
def convertToRgb(col):
    colorRgb = []
    for i in range(0, 3):
        colorRgb.append(math.floor(col[i]))
    return colorRgb


def convertToHex(col):    
    return binascii.hexlify(bytearray(int(c) for c in col)).decode('ascii')


def getHsvForSort(hexrgb):
    hsv = getHsv(hexrgb)
    sat = hsv[1]

    if(sat <= hsv_threshold_white ):
        avg = 255 
        hsv = colorsys.rgb_to_hsv(avg, avg, avg)
    
    if (sat >= (1 - hsv_threshold_black)):
        avg = 0
        hsv = colorsys.rgb_to_hsv(avg, avg, avg)
    
    return hsv


def getHsv(hexrgb):
    hsv = colorsys.rgb_to_hsv(hexrgb[1][0], hexrgb[1][1], hexrgb[1][2])

    return hsv


def mostHsvs(colors):
    # sorteren zodat meest gebruikte kleuren vooraan staan
    colors2 = colors
    colors2.sort(key=lambda x: x[2], reverse=1)
    print("most color = ", colors2[0])
    print("2nd most color = ", colors2[1])

    return (getHsv(colors2[0]), getHsv(colors2[1]))
    


##########################################################
#
#   DB functions
#
##########################################################
def fetchUrls():
    import mysql.connector
    mydb = mysql.connector.connect(
    host="vandewalle.mobi",
    user="homepagecolors",
    passwd="ET7SjuwQFIZF46M4",
    database="homepagecolors"
    )

    mycursor = mydb.cursor()  

    mycursor.execute("SELECT * FROM homepages where fetched = 0 limit 5")
    myresult = mycursor.fetchall()
    return myresult


        
def saveSwapToDb(url, swap):
    import mysql.connector
    mydb = mysql.connector.connect(
    host="vandewalle.mobi",
    user="homepagecolors",
    passwd="ET7SjuwQFIZF46M4",
    database="homepagecolors"
    )

    hue1 = str(round(swap[1][0][0] * 360))
    hue2 = str(round(swap[1][1][0] * 360))

    sat1 = str(round(swap[1][0][1] * 100))
    sat2 = str(round(swap[1][1][1] * 100))
    
    swapFile = swap[0]
    mycursor = mydb.cursor()
    sql = "UPDATE homepages SET date = now(), fetched = 1, mostHue1 = " + hue1 + ", mostHue2 = " + hue2 + ", mostSat1 = " + sat1 + ", mostSat2 = " + sat2 + ", swaps = '" + swapFile + "' WHERE url = '" + url + "'"
    print(sql)
    mycursor.execute(sql)
    mydb.commit()



################################################################
#
#   MAIN
#
################################################################
def main():    
    analyseTest()
    exit(0)

    urls = fetchUrls()
    for url in urls:
        handleUrl(url)


    
if __name__ == "__main__":
    main()