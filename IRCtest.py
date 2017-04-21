#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""
A script that displays the ordinal number of the new articles being created
visible on the Recent Changes list. The script doesn't make any edits, no bot
account needed.

Note: the script requires the Python IRC library
http://python-irclib.sourceforge.net/
"""

# Author: Balasyum
# http://hu.wikipedia.org/wiki/User:Balasyum
# License : LGPL
__version__ = '$Id: 229b3e02cf110f5e9d7f8d16c60906ee9769b7af $'

import re
import threading
from pywikibot import textlib

import pywikibot
import datetime, time
from time import strftime
#import externals
#externals.check_setup('irclib')
import irclib
from ircbot import SingleServerIRCBot

class userPageThread(object):
    """ Threading example class
    The run() method will be started and it will run in the background
    until the application exits.
    """

    def __init__(self, arg):
        """ Constructor
        :type arg: page
        :param arg: page to edit
        """
        self.args = arg
        

        thread = threading.Thread(target=self.run, args=self.args)
        thread.daemon = True                            # Daemonize thread
        thread.start()                                  # Start the execution

    def catsPresent(self,text):
        # check if text contains explicit categories
        catR = re.compile(ur'\[\[kategoria',re.I)
        return (catR.search(text))

    def checkUserPage(self,page):
        text = page.text
        if self.catsPresent(textlib.removeDisabledParts(text)):
            text = textlib.replaceExcept(text, ur'\[\[kategoria', '[[:Kategoria', ['comment','pre','nowiki'], caseInsensitive=True)
            #text = re.sub('\[\[kategoria', '[[:Kategoria', text, flags=re.I)
            pywikibot.output(u'Kategorie usunięte')
            page.text = text
            #page.save(summary=u'Bot usuwa stronę użytkownika z kategorii', apply_cosmetic_changes=False)
        else:
            pywikibot.output(u'Strona użytkownika OK')
        return

    def run(self, arg):
        pywikibot.output('Background USER page %s. Kat:%i Depth:%i, Threads:%s' % (arg.title(), len(list(arg.categories())), arg.depth, threading.activeCount() ))
        if arg.depth > 0:
            self.checkUserPage(arg)



class newArticleThread(object):
    """ Threading example class
    The run() method will be started and it will run in the background
    until the application exits.
    """

    def __init__(self, arg):
        """ Constructor
        :type arg: page
        :param arg: page to edit
        """
        self.args = arg
        

        thread = threading.Thread(target=self.run, args=self.args)
        thread.daemon = True                            # Daemonize thread
        thread.start()                                  # Start the execution

    def catsPresent(self,text):
        # check if text contains explicit categories
        catR = re.compile(ur'\[\[kategoria',re.I)
        return (catR.search(text))

    def linksPresent(self,text):
        # check if text contains explicit wikilinks
        linkR = re.compile(ur'\[\[.*?[\|\]]')
        return (linkR.search(text))

    def spacesPresent(self,text):
        # check if text contains spaces
        return (' ' in text)

    def checkNewArticle(self, page):
        catExists = False
        linksExists = False
        comma = False

        # reget the page after sleep period
        try:
            page.get(force=True)
        except pywikibot.NoPage:
            pywikibot.output(u'Page removed:%s' % page.title())
            return
        else:
            pass

        text = page.text

        #check for obvious experiments
        #if not self.spacesPresent(textlib.removeDisabledParts(text)):
        #    page.text = u'{{ek|artykuł nie zawiera spacji, prawdopodobnie eksperyment edycyjny}}\n' + page.text
        #    page.save(summary=u'{{ek}} - artykuł nie zawiera spacji, prawdopodobnie eksperyment edycyjny')
        #    return


        # check for disambig
        if page.isDisambig() or u'{{Ujednoznacznienie' in page.text or u'{{ujednoznacznienie' in page.text:
            pywikibot.output(u'Disambig:%s' % page.title())
            return
        # check if new page has categories
        if len(list(page.categories())):
            pywikibot.output(u'Kategorie OK:%s' % page.title())
            catExists = True
        elif not self.catsPresent(text):
            pywikibot.output(u'Brak kategorii:%s' % page.title())
        else:
            catExists = True
            pywikibot.output(u'Kategorie OK - API=0')
        # check if new page has wikilinks
        if self.linksPresent(text):
            pywikibot.output(u'Linki OK:%s' % page.title())
            linksExists = True
        else:
            pywikibot.output(u'Brak linków:%s' % page.title())

        pywikibot.output(u'Cat:%s Lnk:%s: Time:%s' % (catExists,linksExists, datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        if not (catExists and linksExists) and not u'{{Dopracować' in page.text:
            templ = u'{{Dopracować'
            summary = u'Sprawdzanie nowych stron, w artykule należy dopracować:'
            if not catExists:
                templ += u'|kategoria='+ datetime.datetime.now().strftime("%Y-%m")
                summary += u' kategorie'
                comma = True
            if not linksExists:
                templ += u'|linki='+ datetime.datetime.now().strftime("%Y-%m")
                if comma:
                    summary += ','
                summary += u'linki'
            templ += u'}}\n'
            page.text = templ + text
            page.save(summary=summary,async=True)
        return

    def run(self, arg):
        pywikibot.output('Background page %s. Kat:%i Depth:%i Time:%s, Threads:%s' % (arg.title(), len(list(arg.categories())), arg.depth, datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), threading.activeCount() ))
        pywikibot.output(u'Waiting ...')
        time.sleep(180)
        self.checkNewArticle(arg)


class ArtNoDisp(SingleServerIRCBot):

    def __init__(self, site, channel, nickname, server, port=6667):
        SingleServerIRCBot.__init__(self, [(server, port)], nickname, nickname)
        self.channel = channel
        self.site = site
        ns = []
        for n in site.namespaces():
            if isinstance(n, tuple):  # I am wondering that this may occur!
                ns += n[0]
            else:
                ns += [n]
        #self.other_ns = re.compile(u'14\[\[07(' + u'|'.join(ns) + u')')
        #self.api_url = self.site.api_address()
        #self.api_url += 'action=query&meta=siteinfo&siprop=statistics&format=xml'
        #self.api_found = re.compile(r'articles="(.*?)"')
        self.re_edit = re.compile(
            r'^C14\[\[^C07(?P<page>.+?)^C14\]\]^C4 (?P<flags>.*?)^C10 ^C02(?P<url>.+?)^C ^C5\*^C ^C03(?P<user>.+?)^C ^C5\*^C \(?^B?(?P<bytes>[+-]?\d+?)^B?\) ^C10(?P<summary>.*)^C'.replace(
                '^B', '\002').replace('^C', '\003').replace('^U', '\037'))

    def on_nicknameinuse(self, c, e):
        c.nick(c.get_nickname() + "_")

    def on_welcome(self, c, e):
        c.join(self.channel)

    def on_privmsg(self, c, e):
        pass

    def on_pubmsg(self, c, e):
        #pywikibot.output(c)
        #pywikibot.output(e)
        source = unicode(e.source().split ( '!' ) [ 0 ], 'utf-8')
        text = unicode(e.arguments() [ 0 ], 'utf-8')
        #pywikibot.output(u'CONNECTION:%s' % unicode(c[ 0 ], 'utf-8'))
        #pywikibot.output(u'SOURCE:%s' % source)
        if u'move' in text:
            pywikibot.output(u'TEXT move:%s' % text)
        
        
        match = self.re_edit.match(e.arguments()[0])
        if not match:
                return

        #if not ('N' in match.group('flags')):
        #        return
        #try:
        #    msg = unicode(e.arguments()[0], 'utf-8')
        #except UnicodeDecodeError:
        #    return
        #pywikibot.output(u'MSG:%s'% msg)
        #print u'******************'
        #print ArtNoDisp.ns
        #print u'******************'

        mpage = unicode(match.group('page'), 'utf-8')        
        mflags = unicode(match.group('flags'), 'utf-8')
        murl = unicode(match.group('url'), 'utf-8')    
        muser = unicode(match.group('user'), 'utf-8')
        mbytes = unicode(match.group('bytes'), 'utf-8')
        msummary = unicode(match.group('summary'), 'utf-8')
        currtime = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        #print (u'P:%s:F:%s:U:%s:B:%s:S:%s:U:%s:T:%s' % (mpage,mflags,muser,mbytes,msummary,murl,currtime)).encode('UTF-8')
        newArt = 'N' in mflags
        page = pywikibot.Page(self.site, mpage)
        #print (u'P:%s:F:%s:U:%s:B:%s:S:%s:U:%s:T:%s:NS:%i' % (mpage,mflags,muser,mbytes,msummary,murl,currtime,page.namespace())).encode('UTF-8')

        if newArt and (page.namespace() == 0):
            # try threading
            if not page.isRedirectPage():
                NAthread = newArticleThread((page,))
            else:
                pywikibot.output(u'skipping')

            #print 'new article'
            #currtime = strftime("%Y-%m-%d %H:%M:%S", datetime.datetime.now().time())
            
            text = self.site.getUrl('https://pl.wikipedia.org/w/api.php?action=query&meta=siteinfo&siprop=statistics&format=xml')
            #print text.encode('UTF-8')
            artsR = re.compile(ur'articles="(?P<arts>.*?)"')
            match = artsR.search(text)
            arts = match.group('arts')
            #pywikibot.output(u'Liczba artykułów:%s' % arts)
            logfile = open("ircbot/artnos.log","a")
            if page.isRedirectPage():
                logline = arts + ';' + currtime + ';R;' + mpage +';' + page.getRedirectTarget().title() + u'\n'
            else:
                logline = arts + ';' + currtime + ';A;' + mpage + u';\n'
            pywikibot.output(logline.encode('UTF-8'))
            logfile.write(logline.encode('UTF-8'))
            logfile.close()
            #print 'look ma, thread is not alive: ', thread.is_alive()
        elif page.namespace() == 2:
            UPthread = userPageThread((page,))
        else:
            pywikibot.output(u'Skipping:%s' % page.title())

    def on_dccmsg(self, c, e):
        pass

    def on_dccchat(self, c, e):
        pass

    def do_command(self, e, cmd):
        pass

    def on_quit(self, e, cmd):
        pass


def main():
    site = pywikibot.getSite()
    #site.forceLogin()
    chan = '#' + site.language() + '.' + site.family.name
    #bot = ArtNoDisp(site, chan, site.loggedInAs(), "irc.wikimedia.org")
    #anlog = fopen('logs/artnos.log','a')
    #logfile = open("artnos.log","a")
    bot = ArtNoDisp(site, chan, 'mastiBotIRC', "irc.wikimedia.org")
    bot.start()
    #try:
    #    bot.start()
    #finally:
    #    logfile.close()
    

if __name__ == "__main__":
    main()
