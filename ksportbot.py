__author__ = 'Kostenloze'

import praw
import re
import time
import requests
import logging
import botconfig
from bs4 import BeautifulSoup as bs

version = '0.5.2-BETA'
logging.basicConfig(filename='ksportbot.log', level=logging.INFO, format='%(levelname)s:%(asctime)s:%(message)s')
logger = logging.getLogger("KSPortBot")


def fetch_link(match):
    name = match.replace("+", "%2B").replace(" ", "+").replace("&", "%26")
    url = "http://kerbalspaceport.com/?s=" + name + "&x=0&y=0&orderby=meta_value_num&meta_key=downloads"
    req = requests.get(url)
    page = bs(req.text)

    results = page.find_all(attrs={'class': "search_item"})
    if len(results) is not 0:
        logger.info('Found a result for %s', match)
        return 'http://kerbalspaceport.com/?p=' + results[0]['id']
    else:
        logger.info('Found no results for %s', match)
        return None


def do_bot():
    r = praw.Reddit('KSPortBot/' + version + ' by /u/Kostenloze')
    r.login(botconfig.username, botconfig.password)

    subreddit = r.get_subreddit('ksportbot+kerbalspaceprogram')
    logger.info('Logged in and got access to the subreddits')
    comments = subreddit.get_comments()

    done = set()
    suitable = 0

    regex = re.compile('LinkMe: ([^\.]+)\.', re.IGNORECASE)
    for comment in comments:
        for reply in comment.replies:
            if reply == '[deleted]' or reply.author is None:
                done.add(comment.id)
            elif reply.author.name.lower() == botconfig.username.lower():
                done.add(comment.id)

        if comment.id not in done and comment.author.name.lower() != botconfig.username.lower():
            reply = []

            for match in regex.findall(comment.body):
                url = fetch_link(match)
                if url is None:
                    reply.append('* Sorry, I could not find ' + match)
                else:
                    reply.append('* [' + match + '](' + url + ')')

            reply.append('\n\n*^This ^bot ^is ^still ^in ^development. ^It ^automatically ^links ^KerbalSpacePort ^Mods'
                         ' ^if ^you ^ask ^it ^to ^do ^so.*'
                         '\n\n*^Message ^/u/Kostenloze ^if ^you ^experience ^any ^issues ^with ^it.*')

            if len(reply) > 1:
                while True:
                    try:
                        comment.reply('\n'.join(reply))
                        done.add(comment.id)
                        logger.info("Posted a reply to the comment with id: %s", comment.id)
                        suitable += 1
                        break
                    except praw.errors.RateLimitExceeded as error:
                        logger.warn("Ratelimited, will sleep for %s and retry to post the comment", error.sleep_time)
                        time.sleep(error.sleep_time)

    if suitable <= 0:
        logger.info("Found no suitable posts this round")
    else:
        logger.info("Found %s suitable posts this round", suitable)


while True:
    logger.info("Starting a new round")
    do_bot()
    logger.info("Finished this round, sleeping for two minutes")
    time.sleep(120)
