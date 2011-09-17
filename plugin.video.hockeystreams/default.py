import urllib, urllib2, re, os, datetime, sys
from BeautifulSoup import BeautifulSoup
from mechanize import Browser
import xbmcplugin, xbmcaddon, xbmcgui

super_verbose_logging = False


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
archivestreams = 'http://hockeystreams.com/hockey_archives'

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
    if year == today.year and month == today.month:
        startday = today.day
    else:
        startday = 31

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

def soupIt(currentUrl, selector, gameType, br = None):
    if (__dbg__):
        if gameType != empty:
            print ("hockeystreams: enter soupIt url %s selector %s gameType %s" % (
            currentUrl, selector, gameType.pattern))
        else:
            print (
            "hockeystreams: enter soupIt  url %s selector %s gameType %s" % (currentUrl, selector, "empty"))

    if br is None:
        br = Browser()
        print ("hockeystreams: empty browser ")
    data = br.open(currentUrl)
    if (__dbg__):
        print ("hockeystreams: \t\tfetch browser result %s %s" % (data, br))

    html = data.read()
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
    #u = url
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
    br = Browser()
    data = br.open(hockeystreams)                                      ##default login page, not passed url
    if (__dbg__ and super_verbose_logging):
        print ("hockeystreams: \t\tfetch login %s %s" % (data, br))
    br.select_form(nr=0)
    br['username'] = username
    br['password'] = password
    data = br.submit()
    if (__dbg__ and super_verbose_logging):
        print ("hockeystreams: \t\tfetch login %s %s" % (data, br))
    return br


def find_qualities(url, br):
    if (__dbg__):
        print ("hockeystreams: \t\t find qs ")

    foundQs = soupIt(url, 'attrs', playbackTypes, br)
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
    #login(username, password, hockeystreams, 'login')
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
    #login(username, password, archivestreams, 'login')
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
    br = login()

    if (__dbg__):
        print ("hockeystreams: enter quality")
    games = find_qualities(url, br)
    for k, v in games.iteritems():
        foundGames = soupIt(v,'input',empty, br)
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

xbmcplugin.endOfDirectory(int(sys.argv[1]), cacheToDisc = cache)


#def getGameNameGamePage(gameType):
#    if (__dbg__):
#        print ("hockeystreams: enter getNameGamePage %s" % (str(gameType)))
#    if gameType in (hqStreams, hdStreams, hdpStreams):
#        foundGames = soupIt(username, password, hockeystreams, 'attrs', gameType)
#    elif gameType in (hqArchives, hdArchives, hdpArchives):
#        archiveDate = createDate()
#        if (__dbg__):
#            print ("hockeystreams: \t\t archive  %s" % (archivestreams + archiveDate))
#        foundGames = soupIt(username, password, archivestreams + archiveDate, 'attrs', gameType)
#    else:
#        foundGames = soupIt(username, password, hockeystreams, 'attrs', gameType)
#    for test in foundGames:
#        if (__dbg__):
#            print ("hockeystreams: \t\t foundGames %s" % (str(test)))
#
#        ending = str(test['href'])
#        gamePage = hockeystreams + ending
#        gameName = os.path.dirname(gamePage)
#        gameName = re.sub('_|/', ' ', gameName)
#
#        if (__dbg__):
#            print ("hockeystreams: \t\t gamename %s" % (gameName))
#        if gameType in (hqStreams, hdStreams, hdpStreams):
#            offset = gameName.index(" live streams ") + len(" live streams ")
#        elif gameType in (hqArchives, hdArchives, hdpArchives):
#            offset = gameName.index(" hockey archives 0 ") + len(" hockey archives 0 ")
#        gameName = gameName[offset:]
#        games[gameName] = gamePage
#    del foundGames
#    return games                                                ##return a dict with game name and page containing direct link


#
#def populateGames(selector):
#    if (__dbg__):
#        print ("hockeystreams: enter populateGames %s" % selector.pattern)
#    populated = getGameNameDirectLink(selector)
#    for k, v in populated.iteritems():
#        addLink(k, '', v, '', 1)


#def getGameNameDirectLink(url, selector):
#    if (__dbg__):
#        print ("hockeystreams: enter getGameNameDirectLink %s" % (str(selector.pattern)))
#    games = getGameNameGamePage(selector)                       ##hqStreams,hdStreams,hdpStreams,etc
#    if (__dbg__):
#        print ("hockeystreams: \t\t games %s" % (str(games)))
#    for k, v in games.iteritems():
#        foundGames = soupIt(username, password, v, 'attrs', playbackTypes)  ##foundGames is BeautifulSoup.resultSet
#        for test in foundGames:                                 ##get rid of this 'busy loop' in the next minor revision
#            #if 'direct_link' in test.get('id',''):
#            directLink = archivestreams + test['href']
#            directLinks[k] = directLink
#    del selector
#    return directLinks
#

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