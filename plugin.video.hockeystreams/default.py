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

__dbg__ = __settings__.getSetting("debug") == "true"
__mark_broken_cdn4_links__ = __settings__.getSetting("mark_cdn4") == "true"

hockeystreams = 'http://www.hockeystreams.com'
archivestreams = hockeystreams + '/hockey_archives'

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
        found.extend(soup.findAll())
    else:
        found = soup.findAll(attrs={'href': gameType})
    del selector
    print "hockeystreams: soupit: found count " + str(len(found))
    return found

def get_date(day, month, year):
    archiveMonth = str(month)
    if len(archiveMonth) == 1:
        archiveMonth = '0' + archiveMonth
    archiveDay = str(day)
    if len(archiveDay) == 1:
        archiveDay = '0' + archiveDay
    archiveDate =  '-'.join([archiveMonth, archiveDay, str(year)])
    return archiveDate

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
        print str("about to add url %s modes %s name %s  directory" % (u, str(mode), name))
        print str("about to add icon: " + icon)
    ok = xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=str(u), listitem=liz, isFolder=True, totalItems=count)
    return ok

def addLink(name, gamename, date, url, icon, count):
    u = sys.argv[0] + "?url=" + urllib.quote_plus(url) + "&mode=2000&name=" + urllib.quote_plus(name) + \
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
    if not __settings__.getSetting('username') or not __settings__.getSetting('password'):
        __settings__.openSettings()
        return False
    if not weblogin.doLogin(cookiepath, __settings__.getSetting('username'), __settings__.getSetting('password'), __dbg__):
        if (__dbg__):
            print ("hockeystreams: login fail")
        return False
    return True


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

def CATEGORIES():
    if (__dbg__):
        print ("hockeystreams: enter categories")
    addDir('Live Streams', hockeystreams, 1, '', 1)
    addDir('Archived By Date', hockeystreams, 2, '', 1)
    addDir('Archived By Team', hockeystreams, 30, '', 1)
    addDir('  Login', hockeystreams, 66, '', 1)
    addDir('  IP Exception', hockeystreams, 99, '', 1)
    
    #addDir('RSS Streams', hockeystreams, 3, '', 1)

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

def ARCHIVE_GAMES_BY_DATE(year, month, day, mode):
    if (__dbg__):
        print ("hockeystreams: enter archive games")
    archiveDate = get_date(day, month, year)
    url = archivestreams + '/' + archiveDate + '/'
    strip = ARCHIVE_STRIP
    games = find_hockey_game_names(url, hqArchives)
    for k, v in games.iteritems():
        gameName = k
        offset = gameName.index(strip) + len(strip)
        gameName = gameName[offset:]
        addDir(gameName, v, mode, '', 1, gamename = gameName)

def BY_TEAM(url, mode):
    if (__dbg__):
        print ("hockeystreams: enter team")
    archiveDate = get_date(today.day, today.month, today.year)
    teamNames = re.compile('/hockey_archives/'+ archiveDate + '/[a-z]+_?[a-z]?') #simplified
    foundTeams = soupIt(url + "/" + archiveDate, "attrs", teamNames)
    for team in foundTeams:
        if (__dbg__):
            print ("hockeystreams: \t\t soupfound team %s" % (str(team)))

        ending = str(team['href'])
        teamPage = hockeystreams + ending
        teamName = os.path.basename(teamPage)
        teamName = re.sub('_|/', ' ', teamName)
        if (__dbg__):
            print ("hockeystreams: \t\t team %s" % teamName)

        teamGIF = hockeystreams + "/images/teams/" + teamName[0:teamName.find(' ')] + ".gif"
        addDir(teamName, teamPage, mode, teamGIF, 82)

def ARCHIVE_GAMES_BY_TEAM(url, mode):
    if (__dbg__):
        print ("hockeystreams: enter archive games")
    strip = ARCHIVE_STRIP
    games = find_hockey_game_names(url, hqArchives)
    for k, v in games.iteritems():
        gameName = k
        offset = gameName.find(strip) + len(strip)
        gameName = gameName[offset:]
        addDir(gameName, v, mode, '', 1000, gamename = gameName)

def QUALITY(url, gamename):
    if (__dbg__):
        print ("hockeystreams: enter quality")
    games = find_qualities(url)
    silverLinks = {}
    for k, v in games.iteritems():
        if (__dbg__):
            print str(games)
        
        foundGames = soupIt(v,'input',empty, True)
        for test in foundGames:                                 ##get rid of this 'busy loop' in the next minor revision
            if (__dbg__):
                print("hockeystreams: \t\t soupfound directs %s" % (test))
            if 'direct_link' in test.get('id',''):
                directLink = test['value']
                directLinks[k] = directLink
            if 'silverlight' in test.get('href',''):
                print "silverBOO"
                silverLink = test.get('href','')
                silverLinks["silverlight"] = silverLink

    for name,url in directLinks.iteritems():
        qualityName = name #name[name.rindex('/'):]
        if __mark_broken_cdn4_links__ and 'cdn-a-4' in url:
            qualityName += "*"
        addLink(qualityName, gamename, '', url, '', 1)
    for name,url in silverLinks.iteritems():
        addLink("has " + name, name, '', url, '', 1)

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
if mode is None or mode == 0 or url is None or len(url) < 1:
    CATEGORIES()
elif mode == 1:
    LIVE_GAMES(1000)
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
    ARCHIVE_GAMES_BY_DATE(year, month, day, 1000)
    cache = not (today.year == year and today.month == month and today.day == day)
elif mode == 30:
    BY_TEAM(archivestreams, 31)
elif mode == 31:
    ARCHIVE_GAMES_BY_TEAM(url, 1000)
elif mode == 1000:
    QUALITY(url, gamename)
    cache = False
elif mode == 2000:
    PLAY_VIDEO(url)
    cache = not (today.year == year and today.month == month and today.day == day)

elif mode == 66:
    if not login():
        print "failed"
        addDir('failed!', hockeystreams, 0, '', 5)
    else:
        addDir('succeeded!', hockeystreams, 0, '', 5)
elif mode == 99:
    if not login():
        addDir('failed!', hockeystreams, 0, '', 5)
    else:
        exception_data = urllib.urlencode({'update': 'Update Exception'})
        exception_url = hockeystreams + "/include/exception.inc.php?" + exception_data
        read = gethtml.get(exception_url, cookiepath)
        addDir('succeeded!', hockeystreams, 0, '', 5)

if mode == 69:
    #xbmcplugin.openSettings(sys.argv[0])
    pass
else:
    xbmcplugin.endOfDirectory(int(sys.argv[1]), cacheToDisc = cache)
