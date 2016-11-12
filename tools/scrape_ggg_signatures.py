#! /usr/bin/env python

# Find the signatures of all games commented on
# view-source:https://gogameguru.com/get-better-at-go/commented-go-games/
# for inclusion in the Kombilo references file
#
# Requires "pip install beautifulsoup4 requests"
#
# Usage: ./scrape_ggg_signatures.py
# writes a comma-separated list of all signatures found to stdout
#
# Note that the script might break if the way the gogameguru web site is
# organized changed. Last used: November 2016.
#
# TODO: handle duplicates more carefully(?)


import os
import requests
from bs4 import BeautifulSoup

from kombilo.kombiloNG import *


def find_links_to_indiv_games(page):
    divs = page.find_all('div', 'entry-content')
    ax = [d.find_all('a', href=True) for d in divs]
    return [a['href'] for al in ax for a in al]


def retrieve_sgf(page):
    def is_link_to_sgf(tag):
        try:
            return tag.text.startswith('Download SGF')
        except AttributeError:
            return False
    try:
        return page.find(is_link_to_sgf)['href']
    except:
        pass


# -------------------------------------------------

try:
    os.system('rm -rf ./ggg_sgfs')
except IOError:
    pass
try:
    os.mkdir('./ggg_sgfs')
except IOError:
    pass

comment_links = []

url = "http://gogameguru.com/get-better-at-go/commented-go-games/"
content = requests.get(url, headers={'user-agent': 'kombilo 0.8', }).content

soup = BeautifulSoup(content, "html.parser")

# find out how many pages of commentary there are
d = soup.find('div', 'navigation')
ul = d.find('ul')
lis = ul.find_all('li')
num_pages = int(lis[-2].find('a').text)

# first page
comment_links += find_links_to_indiv_games(soup)

for i in range(2, num_pages+1):
    content = requests.get(url + 'page/%d/' % i, headers={'user-agent': 'kombilo 0.8', }).content
    soup = BeautifulSoup(content, "html.parser")
    comment_links += find_links_to_indiv_games(soup)


for ctr, link in enumerate(comment_links):
    content = requests.get(link, headers={'user-agent': 'kombilo 0.8', }).content
    sgf_link = retrieve_sgf(BeautifulSoup(content, 'html.parser'))
    if not sgf_link:
        print 'no download link found', link
        continue
    sgf = requests.get(sgf_link, headers={'user-agent': 'kombilo 0.8', }).content

    with open('./ggg_sgfs/sgf%d.sgf' % ctr, 'w') as f:
        f.write(sgf)


K = KEngine()
K.addDB('./ggg_sgfs', acceptDupl=False)

for i in range(K.gamelist.noOfGames()):
    print(K.gamelist.printSignature(i) + ',')

