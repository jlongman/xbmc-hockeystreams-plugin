import weblogin, gethtml

import urllib, re, os, datetime, sys
from BeautifulSoup import BeautifulSoup
import xbmcplugin, xbmcaddon, xbmcgui

super_verbose_logging = False

__addonname__ = 'plugin.video.hockeystreams'
__datapath__ = os.path.join('special://profile/addon_data/',__addonname__)

#important! deals with a bug where errors are thrown if directory does not exist.
if not os.path.exists: os.makedirs(__datapath__)
cookiepath = __datapath__


__plugin__ = "Hockeystreams"
__author__ = "Fe4r"
__version__ = "1.3.1"
__url__ = "http://code.google.com/p/xbmc-hockeystreams/"
__svn__ = "http://xbmc-hockeystreams.googlecode.com/svn/trunk/"
__svn_revision__ = "$Revision$"
__settings__ = xbmcaddon.Addon(id='plugin.video.hockeystreams')

username = __settings__.getSetting('username')
password = __settings__.getSetting('password')
__dbg__ = __settings__.getSetting("debug") == "true"

hockeystreams = 'http://www.hockeystreams.com'
archivestreams = 'http://www.hockeystreams.com/hockey_archives'

hqStreams = re.compile('/live_streams/.*')
hqArchives = re.compile('/hockey_archives/0/.*/[0-9]+')
playbackTypes = re.compile('/hockey_archives/0/.*/[0-9]+/[a-z_]+')

today = datetime.date.today()

ARCHIVE_STRIP = " hockey archives 0 "
LIVE_STRIP = " live streams "

empty = None
directLinks = {}
games = {}

def YEAR(url, mode):
    for year in range(today.year, 2009, -1):
        if year == today.year:
            monthsCount = today.month
        else:
            monthsCount = 12
        addDir(str(year), url, mode, '', monthsCount, year)

def MONTH(url, year, mode):
    if year == today.year:
        startmonth = today.month
    else:
        startmonth = 12
    for month in range(startmonth, 0, -1):
        patsy = datetime.date(int(year), int(month), 1)
        days_in_month = int(patsy.strftime("%d"))
        if month == patsy.month:
            daysCount = today.day
        else:
            daysCount = days_in_month
        addDir(patsy.strftime("%B"), url, mode, '', daysCount, year, month)

def DAY(url, year, month, mode):
    startday = 31
    if year == today.year and month == today.month:
        startday = today.day

    for day in range(startday, 0, -1):
        try:
            patsy = datetime.date(year, month, day)
            addDir(patsy.strftime("%x"), url, mode, '', 1, year, month, day)
        except ValueError:
            pass # skip day


def get_params():
    param = {}
    paramstring = sys.argv[2]
    if(len(paramstring) >= 2):
        params = sys.argv[2]
        cleanedparams = params.replace('?', '')
        if(params[len(params) - 1] == '/'):
            params = params[0:len(params) - 2]
        pairsOfParams = cleanedparams.split('&')
        for i in range(len(pairsOfParams)):
            splitParams = pairsOfParams[i].split('=')
            if(len(splitParams) == 2):
                param[splitParams[0]] = splitParams[1]
    return param

def soupIt(currentUrl, selector, gameType, loginRequired = False):
    if (__dbg__):
        if gameType != empty:
            print ("hockeystreams: enter soupIt url %s selector %s gameType %s" % (
            currentUrl, selector, gameType.pattern))
        else:
            print (
            "hockeystreams: enter soupIt  url %s selector %s gameType %s" % (currentUrl, selector, "empty"))
    if loginRequired:
        html = gethtml.get(currentUrl, cookiepath)
    else:
        html = gethtml.get(currentUrl)

    if (__dbg__ and super_verbose_logging):
        print ("hockeystreams: \t\tfetch browser result %s " % html)

    
    if (__dbg__):
        print ("hockeystreams: \t\t soupIt %s " % html)
    soup = BeautifulSoup(''.join(html))

    if selector == 'input':
        found = soup.findAll('input')
    else:
        found = soup.findAll(attrs={'href': gameType})
    del selector
    return found



def CATEGORIES():
    #login(username, password, currentUrl, 'login')
    if (__dbg__):
        print ("hockeystreams: enter categories")
    addDir('Live Streams', hockeystreams, 1, '', 1)
    addDir('Archived Streams', hockeystreams, 2, '', 1)
    addDir('Login', hockeystreams, 66, '', 1)
    addDir('IP Exception', hockeystreams, 99, '', 1)
    addDir('Settings', hockeystreams, 69, '', 1)
    #addDir('RSS Streams', hockeystreams, 3, '', 1)

def addDir(name, url, mode, icon, count, year=-1, month=-1, day=-1, gamename = None):
    u = sys.argv[0] + "?url=" + urllib.quote_plus(url) + "&mode=" + str(mode) + "&name=" + urllib.quote_plus(name)
    if gamename is not None:
        u += "&gamename=" + urllib.quote_plus(gamename)
    if year > 0:
        u += "&year=" + str(year)
        if month > 0:
            u += "&month=" + str(month)
            if day > 0:
                u += "&day=" + str(day)
    liz = xbmcgui.ListItem(name, iconImage=icon, thumbnailImage=icon)
    liz.setInfo(type="Video", infoLabels={"Title": name})
    if (__dbg__):
        print str("about to add url %s directory" % (str(u)))
        print str("about to add modes %s  directory" % (str(mode)))
        print str("about to add name %s  directory" % (str(name)))
    ok = xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=str(u), listitem=liz, isFolder=True, totalItems=count)
    return ok

def addLink(name, gamename, date, url, icon, count):
    u = sys.argv[0] + "?url=" + urllib.quote_plus(url) + "&mode=20&name=" + urllib.quote_plus(name) + \
        "&gamename=" + urllib.quote_plus(gamename)
    liz = xbmcgui.ListItem(name, iconImage=icon, thumbnailImage=icon)
    liz.setInfo(type="Video", infoLabels={"Title": name, "Date": date})
    liz.setProperty('isPlayable', 'true')
    if (__dbg__):
        print ("about to add %s %s %d link" % (name, u, int(count)))
    ok = xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, liz, isFolder=False, totalItems=count)
    return ok

def find_hockey_game_names(url, gameType):
    foundGames = soupIt(url, 'attrs', gameType)
    for test in foundGames:
        if (__dbg__):
            print ("hockeystreams: \t\t foundGames %s" % (str(test)))

        ending = str(test['href'])
        gamePage = hockeystreams + ending
        gameName = os.path.dirname(gamePage)
        gameName = re.sub('_|/', ' ', gameName)

        if (__dbg__):
            print ("hockeystreams: \t\t gamename %s" % gameName)
        games[gameName] = gamePage
    del foundGames
    return games


def login():
    if (__dbg__):
        print ("hockeystreams: login attempt")
    if not weblogin.doLogin(cookiepath, username, password):
        if (__dbg__):
            print ("hockeystreams: login fail")
        return


def find_qualities(url):
    if (__dbg__):
        print ("hockeystreams: \t\t find qs ")

    foundQs = soupIt(url, 'attrs', playbackTypes, True)
    for test in foundQs:
        if (__dbg__):
            print ("hockeystreams: \t\t soupfound qs %s" % (str(test)))

        ending = str(test['href'])
        gamePage = hockeystreams + ending
        gameName = os.path.basename(gamePage)
        gameName = re.sub('_|/', ' ', gameName)
        if (__dbg__):
            print ("hockeystreams: \t\t q: %s" % gameName)
        games[gameName] = gamePage
    del foundQs
    return games

def LIVE_GAMES(mode):
    if (__dbg__):
        print ("hockeystreams: enter live games")
    url = hockeystreams
    strip = LIVE_STRIP
    games = find_hockey_game_names(url, hqStreams)
    for k, v in games.iteritems():
        gameName = k
        offset = gameName.index(strip) + len(strip)
        gameName = gameName[offset:]
        addDir(gameName, v, mode, '', 1, gamename = gameName)

def ARCHIVE_GAMES(year, month, day, mode):
    if (__dbg__):
        print ("hockeystreams: enter archive games")
    archiveMonth = str(month)
    if len(archiveMonth) == 1:
        archiveMonth = '0' + archiveMonth
    archiveDay = str(day)
    if len(archiveDay) == 1:
        archiveDay = '0' + archiveDay
    archiveDate = "/" + '-'.join([archiveMonth, archiveDay, str(year)]) + "/"
    url = archivestreams + archiveDate
    strip = ARCHIVE_STRIP
    games = find_hockey_game_names(url, hqArchives)
    for k, v in games.iteritems():
        gameName = k
        offset = gameName.index(strip) + len(strip)
        gameName = gameName[offset:]
        addDir(gameName, v, mode, '', 1, gamename = gameName)

def QUALITY(url, gamename):

    if (__dbg__):
        print ("hockeystreams: enter quality")
    games = find_qualities(url)
    for k, v in games.iteritems():
        foundGames = soupIt(v,'input',empty, True)
        for test in foundGames:                                 ##get rid of this 'busy loop' in the next minor revision
            if (__dbg__):
                print("hockeystreams: \t\t soupfound directs %s" % (test))
            if 'direct_link' in test.get('id',''):
                directLink = test['value']
                directLinks[k] = directLink
    for name,url in directLinks.iteritems():
        qualityName = name #name[name.rindex('/'):]
        addLink(qualityName, gamename, '', url, '', 1)

def PLAY_VIDEO(video_url):
    if (__dbg__):
        print ("hockeystreams: enter play")
    # cool, got it, now create and open the video
    liz = xbmcgui.ListItem(name, path = video_url)
    liz.setInfo(type = "Video", infoLabels = {"Title": gamename})
    liz.setProperty('isPlayable', 'true')
    xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, liz)

params = get_params()
gamename = None
url = None
name = None
mode = None
year = None
month = None
day = None

try:
    url = urllib.unquote_plus(params['url'])
except:
    pass
try:
    name = urllib.unquote_plus(params['name'])
except:
    pass
try:
    gamename = urllib.unquote_plus(params['gamename'])
except:
    pass

try:
    mode = int(params['mode'])
except:
    pass

try:
    year = int(params['year'])
    month = int(params['month'])
    day = int(params['day'])
except:
    pass

if (__dbg__):
    print ("url %s name %s mode %s" % (url, name, mode))
    print ("year %s month %s day %s" % (year, month, day))

cache = True
if mode is None or url is None or len(url) < 1:
    CATEGORIES()
elif mode == 1:
    LIVE_GAMES(6)
    cache = False
elif mode == 2:
    YEAR(hockeystreams, 3)
    cache = False
elif mode == 3:
    MONTH(hockeystreams, year, 4)
    cache = today.year != year
elif mode == 4:
    DAY(hockeystreams, year, month, 5)
    cache = not (today.year == year and today.month == month)
elif mode == 5:
    ARCHIVE_GAMES(year, month, day, 6)
    cache = not (today.year == year and today.month == month and today.day == day)
elif mode == 6:
    QUALITY(url, gamename)
    cache = False
elif mode == 20:
    PLAY_VIDEO(url)
    cache = not (today.year == year and today.month == month and today.day == day)
elif mode == 66:
    if not login():
        print "failed"

elif mode == 99:
    login()
    exception_data = urllib.urlencode({'update': 'Update Exception'})
    exception_url = hockeystreams + "/include/exception.inc.php?" + exception_data
    read = gethtml.get(exception_url, cookiepath)



##rss stuff
##---------------------------------------------------

##elif mode >= 10:
##    import rssArchives
##    if mode == 10:
##        rssArchives.populateRSS('hq')
##    elif mode == 11:
##        rssArchives.populateRSS('hd')
##    elif mode == 12:
##        rssArchives.populateRSS('hdp')

##---------------------------------------------------
##end of rss stuff
if mode == 69:
    xbmcplugin.openSettings(sys.argv[0])
else:
    xbmcplugin.endOfDirectory(int(sys.argv[1]), cacheToDisc = cache)


#def retrieveUrl(url, referer):
#	req = urllib2.Request(url)
#	req.add_header("User-Agent", "Mozilla/5.0 (X11; U; Linux x86_64; en-US; rv:1.9.2.3) Gecko/20100402 Namoroka/3.6.3")
#	req.add_header("Accept", "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8")
#	req.add_header("Accept-Language", "en-us,en;q=0.5")
#	req.add_header("Accept-Encoding", "deflate")
#	req.add_header("Accept-Charset", "ISO-8859-1,utf-8;q=0.7,*;q=0.7")
#	if(referer != ""):
#		req.add_header("Referer", referer)
#	response = urllib2.urlopen(req)
#	file = response.read()
#	response.close()
#	return file