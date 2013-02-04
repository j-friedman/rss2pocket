#!/usr/bin/python
#
# rss2pocket
# 
# A handy script to read RSS feeds and email them to a pocket account.
#
# $Last Modified: Thu Nov 29, 2012  09:47PM

import feedparser
import datetime
import argparse
import pickle
import sys
import subprocess
import StringIO
from os.path import expanduser
from time import localtime, strftime
from email.mime.text import MIMEText

__version__ = "0.01"
__author__ = "Jonathan Friedman (jonf@gojon.com)"
__copyright__ = "(C) 2012 Jonathan Friedman under the GNU GPL3"

config = { 'feed_list': [] }


def get_new_entries(feed):
   feed_url = feed[0]
   last_updt = feed[1]
   f = feedparser.parse(feed_url)
   new_entries = []

   for e in f.entries:
      if e.has_key('updated_parsed') and e.updated_parsed > last_updt:
         new_entries.append(e)
         last_updt = e.updated_parsed
      elif e.has_key('published_parsed') and e.published_parsed > last_updt:
         new_entries.append(e)
         last_updt = e.published_parsed

   return (new_entries, (feed_url, localtime())) #last_updt))


def save_config():
   f = open(expanduser('~') + '/.rss2pocket', 'w')
   pickle.dump(config, f)
   f.close()


def send_entry(sender, entry):
   msg = MIMEText(entry.link)
   
   msg['Subject'] = entry.title
   msg['From'] = sender
   msg['To'] = 'add@getpocket.com'

   print 'sending ' + entry.link,
   p = subprocess.Popen(['sendmail', '-t', 'add@getpocket.com'], stdout=subprocess.PIPE, stdin=subprocess.PIPE)
   output = p.communicate(msg.as_string())[0]
   print output + ' done'
 

if __name__ == '__main__':
   # make sure to see if .rss2pocket exists, the Right Way(tm). If it doesn't,
   # then create it with the defaults.
   try:
      config = pickle.load(open(expanduser('~') + '/.rss2pocket'))
   except IOError as e:
      pass

   arg_parser = argparse.ArgumentParser(description='Send RSS feeds to a Pocket account.')
   group = arg_parser.add_mutually_exclusive_group()
   group.add_argument('-a', '--add', action='store', help='add url for another feed')
   group.add_argument('-l', '--list', action='store_true', help='list feeds')
   group.add_argument('-d', '--delete', action='store', help='delete feed from list')
   group.add_argument('-r', '--run', action='store_true', help='fetch and deliver feeds')
   group.add_argument('-e', '--email', action='store', help='set sender email address')

   args = arg_parser.parse_args()
   
   print vars(args)

   if vars(args)['email']:
      config['from'] = vars(args)['email']
      save_config()

   if vars(args)['list']:
      if len(config['feed_list']) == 0:
         print 'no feeds added (yet)'
         sys.exit(0)

      if config.has_key('from'):
         print 'sending from: ' + config['from']
      else:
         print 'no sender set!'

      for i in range(len(config['feed_list'])):
         feed = config['feed_list'][i]
         print "%03d: %s" % (i + 1, feed[0])

   if vars(args)['add']:
      url = vars(args)['add']
      if not url in [ e[0] for e in config['feed_list'] ]:
         config['feed_list'].append((url, localtime(1)))
      else:
         print url + ' already in the list, skipping'

      save_config()

   if vars(args)['delete']:
      i = int(vars(args)['delete']) - 1
      print 'removed ' + config['feed_list'][i][0]

      del config['feed_list'][i]

      save_config()

   if vars(args)['run']:
      new_feed_list = []
      new_entries = []

      if not config.has_key('from'):
         print 'set the sender email before running!'
         sys.exit(1)

      for i in range(len(config['feed_list'])):
         (entries, new_feed) = get_new_entries(config['feed_list'][i])
         new_entries = new_entries + entries
         new_feed_list.append(new_feed)

         if len(new_entries) > 0:
            print str(len(new_entries)) + ' new entries found for ' + new_feed[0]

      for e in new_entries:
         send_entry(config['from'], e)

      config['feed_list'] = new_feed_list  
      save_config()
