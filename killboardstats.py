#!/usr/bin/env python
import urllib2
import urllib
import json
import sys
import exceptions
import locale
import config
import systems
import ships
from datetime import datetime
import time
import os
import signal

def run_zkillstats(config_type, config_id):
    pull_stats = 'https://zkillboard.com/api/stats/{0}/'.format(config_type)

    locale.setlocale(locale.LC_ALL, config.config_locale)

    request = urllib2.Request(pull_stats)
    request.add_header('User-Agent', config.config_header)
    opener = urllib2.build_opener()
    data = opener.open(request)
    root = json.load(data)


## handled kills needs to become `past monthly summaries` so that only the newest last month is displayed for the summary

    handled_kills = []
    f = open('handled_kills.dat', 'r+')
    for line in f:
        handled_kills.append(line.rstrip('\n'))

    for data in root:
        try:
            kill_id = data['killID']
            if str(kill_id) in handled_kills:
                continue
            

            attachment = {}
            stats = {}
            allTimeSum = {}
            allTimeISKdestroyed = {}
            allTimeISKdelta = {}

#      
#            if killer['characterID'] == 0:
#                killerName = killer['shipTypeID']
#            else:
#                killerName = killer['characterName']
#            if victim['characterID'] == 0:
#                victimName = victim['shipTypeID']
#            else:
#                victimName = victim['characterName']
#            
#            if victim[config_type] == config_id:
#                kill['URL_text'] = '{0} [{1}] >> [{2}] got killed by {3} [{4}] >> [{5}]'.format(victimName, victim['corporationName'], victim['allianceName'], killerName, killer['corporationName'], killer['allianceName']) 
#                kill['color'] = 'danger'
#                damageTaken['title'] = "Damage taken"
#            else:
#                kill['URL_text'] = '{0} [{1}] >> [{2}] killed {3} [{4}] >> [{5}]'.format(killerName, killer['corporationName'], killer['allianceName'], victimName, victim['corporationName'], victim['allianceName'])
#                kill['color'] = 'good'
#                damageTaken['title'] = "Damage dealt"
#
            stats['pretext'] = '*Monthly statistics -- {0} {1}*'.format("'data['month'], data['year']")
            stats['URL_text'] = '{0} {1} [{2}]'.format(data['corporationName'], data['allianceName'])
            stats['title'] = stats['URL_text']
            stats['title_link'] = 'https://zkillboard.com/api/stats/{0}/'.format(config_type)
            stats['thumb_url'] = 'https://imageserver.eveonline.com/{0}/{1}_128.png'.format(config_type, config_id)
            stats['color'] = '#439FE0'
            
            
            allTimeSum['title'] = 'All Time Kills' 
            allTimeSum['value'] = 'allTimeSum'
            allTimeSum['short'] = "true"
            
            allTimeISKdestroyed['title'] = 'Total ISK Destroyed'
            allTimeISKdestroyed['value'] = locale.format('%d', data['iskDestroyed'], grouping=True)
            allTimeISKdestroyed['short'] = "true"

            allTimeISKlost['title'] = 'Total ISK Lost'
            allTimeISKlost['value'] = locale.format('%d', data['iskLost'], grouping=True)
            allTimeISKlost['short'] = "true"

            allTimeISKdelta['title'] = 'Total ISK Lost'
            allTimeISKdelta['value'] = locale.format('%d', (data['iskDestroyed'] - data['iskLost']), grouping=True)
            allTimeISKdelta['short'] = "true"
            
            
            stats['fields'] = [allTimeSum, allTimeISKdestroyed, allTimeISKlost, allTimeISKdelta]
            
            attachment['attachments'] = [stats]
            
            payload = json.dumps(attachment)
            
            data = urllib.urlencode({'payload': payload})
            
            request_slack = urllib2.Request(config.config_slack_url, data)
            urllib2.urlopen(request_slack)

            time.sleep(2)
            f.write('{0}\n'.format(kill_id))
        except urllib2.HTTPError as e:
            print "HTTPError in processing data: " + str(e.reason)
        except exceptions.KeyError as e:
            print "KeyError in processing data: " + str(e)
        except exceptions.NameError as e:
            print "NameError in processing data: " + str(e)
        except Exception:
            print "Generic Exception in processing data: " + str(sys.exc_info()[0]) + " (" + str(sys.exc_info()[1]) + ")"
        
    f.close()
    
def make_pid():
    try:
        os.stat('/var/run')
    except:
        os.mkdir('/var/run')
    f = open('/var/run/kbbot.pid', 'w+')
    f.truncate()
    f.write(str(os.getpid()))
    f.write("\n");
    f.close()

def signal_handler(signal, frame):
    os.remove('/var/run/kbbot.pid')
    exit()

if config.config_run_as_daemon:
	make_pid()
	signal.signal(signal.SIGINT, signal_handler)

while True:
    try:
        for group in config.config_owner:
            for key,val in group.items():
                run_zkillstats(key, val)
            time.sleep(60)
        time.sleep(config.config_sleep_time)
    except urllib2.HTTPError as e:
        print "HTTPError in processing killboard data: " + str(e.reason)
        time.sleep(60)
    except Exception:
        print "Exception in processing killboard data: " + str(sys.exc_info()[0]) + " (" + str(sys.exc_info()[1]) + ")"
        time.sleep(60)
