################################################################
#
#   INTRO
#
################################################################
# test program to convert html page to image

################################################################
#
#   IMPORTS
#
################################################################
import time


screenshot_delay = 5
################################################################
#
#   PROGRAM
#
################################################################
def urlToImg(url):
    from selenium import webdriver

    filename = urlToFilename(url)
    driver = webdriver.PhantomJS()
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


################################################################
#
#   MAIN
#
################################################################
urlToImg("https://www.spotify.com")