from xml.dom import minidom
import re
import time

__author__ = 'longman'


def getText(nodelist):
    rc = []
    for node in nodelist:
        if node.nodeType == node.TEXT_NODE:
            rc.append(node.data)
    return ''.join(rc)

def get_live_streams(rssBody, __debug__) :
    gameDom = minidom.parse(rssBody)
    games = []
    for game in gameDom.getElementsByTagName('item'):
        title = getText(game.getElementsByTagName('title')[0].childNodes)
        description = getText(game.getElementsByTagName('description')[0].childNodes)
#        if __debug__:
        print "title " + title + " description " + description
        date, rest = description.split('<', 1)
#        if __debug__:
        date = date.strip()
        print "date " + date + "rest " + rest
        match = re.search( 'href="(http://.*?[0-9]+/)[a-z_]+"', rest)
        url = match.group(1)
#        if __debug__:
        real_date = time.strptime(date, "%m/%d/%Y - %I:%M %p")
        print "url " + url
        games.append(
            (title, url, date, real_date )
        )
        
    return games


