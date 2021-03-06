#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""
A script that displays the ordinal number of the new articles being created visible on the Recent Changes list.
The script doesn't make any edits, no bot account needed.

Note: the script requires the Python IRC library http://python-irclib.sourceforge.net/

Bot outputs in a form of:
ArtID datetime A/R ArtTitle
where A is for article, R for Redirect

"""

# Author: Balasyum
# http://hu.wikipedia.org/wiki/User:Balasyum
# License : LGPL
__version__ = '$Id: articlenos.py 6905 2009-05-19 10:49:38Z cosoleto $'

from ircbot import SingleServerIRCBot
from irclib import nm_to_n, nm_to_h, irc_lower, ip_numstr_to_quad, ip_quad_to_numstr
import wikipedia
import re

class ArtNoDisp(SingleServerIRCBot):
    def __init__(self, site, channel, nickname, server, port=6667):
        SingleServerIRCBot.__init__(self, [(server, port)], nickname, nickname)
        self.channel = channel
        self.site = site
        self.other_ns = re.compile(u'14\[\[07(' + u'|'.join(site.namespaces()) + u')')
        self.api_url = self.site.api_address()
        self.api_url += 'action=query&meta=siteinfo&siprop=statistics&format=xml'
        self.api_found = re.compile(r'articles="(.*?)"')
        self.re_edit = re.compile(r'^C14\[\[^C07(?P<page>.+?)^C14\]\]^C4 (?P<flags>.*?)^C10 ^C02(?P<url>.+?)^C ^C5\*^C ^C03(?P<user>.+?)^C ^C5\*^C \(?^B?(?P<bytes>[+-]?\d+?)^B?\) ^C10(?P<summary>.*)^C'.replace('^B', '\002').replace('^C', '\003').replace('^U', '\037'))

    def on_nicknameinuse(self, c, e):
        c.nick(c.get_nickname() + "_")

    def on_welcome(self, c, e):
        c.join(self.channel)

    def on_privmsg(self, c, e):
        pass

    def on_pubmsg(self, c, e):
        pywikibot.output(u'%s' % e)
        pywikibot.output(u'<eargs>%s' % e.arguments()[0])
        return
        match = self.re_edit.match(e.arguments()[0])
        if not match:
                return
        if not ('N' in match.group('flags')):
                return
        try:
            msg = unicode(e.arguments()[0],'utf-8')
        except UnicodeDecodeError:
            wikipedia.output(u'UnicodeDecodeError')
            return
        if self.other_ns.match(msg):
            return
        name = msg[8:msg.find(u'14',9)]
        text = self.site.getUrl(self.api_url)
        entry = self.api_found.findall(text)
        page = wikipedia.Page(self.site, name)
        try:
                text = page.get()
        except wikipedia.NoPage:
                return
        except wikipedia.IsRedirectPage:
                #print entry[0], name, u'*Redirect*'
                #log = entry[0] + name + u'*Redirect*'
                wikipedia.output(u'%s %s R [[%s]]' % (entry[0], page.editTime(), name))
                #wikipedia.log( log )
                return
        #print entry[0], name
	#log = entry[0] + name
	wikipedia.output(u'%s %s A [[%s]]' % (entry[0], page.editTime(), name))
	#wikipedia.log( log )

    def on_dccmsg(self, c, e):
        pass

    def on_dccchat(self, c, e):
        pass

    def do_command(self, e, cmd):
        pass

    def on_quit(self, e, cmd):
        pass

def main():
    wikipedia.handleArgs()
    site = wikipedia.getSite()
    site.forceLogin()
    chan = '#' + site.language() + '.' + site.family.name
    bot = ArtNoDisp(site, chan, site.loggedInAs(), "irc.wikimedia.org")
    bot.start()

if __name__ == "__main__":
    main()
