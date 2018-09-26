import httplib
import os
import urllib2
import webbrowser

import regex
from bs4 import BeautifulSoup

import sample.database
import sample.html_format

httplib.HTTPConnection._http_vsn = 10
httplib.HTTPConnection._http_vsn_str = 'HTTP/1.0'


def register(email, keywords):
    user = sample.database.create_user(email)
    _append_keywords_to_user(user, keywords)


def add_keyword(email, keywords):
    user = sample.database.find_by_email(email)
    _append_keywords_to_user(user, keywords)


def _append_keywords_to_user(user, keywords):
    search_text = '+'.join(keywords.split())
    response = urllib2.urlopen("https://fr.pornhub.com/video/search?search=" + search_text + "&o=mr")
    page_source = response.read()
    soup = BeautifulSoup(page_source, "html.parser")
    ul = soup.find('ul', class_=regex.compile('videos search-video-thumbs'))

    first_key = None
    for li in ul.find_all('li'):
        current = li['_vkey']
        if not first_key: first_key = current
        checked = li.find('span', {'class': 'own-video-thumbnail main-sprite tooltipTrig'})
        if checked:
            user.append_user_search_text(search_text, first_key, current)
            user.save()
            break


def search(email):
    user = sample.database.find_by_email(email)
    result_by_keyword = {}
    for keyword in user.keyword_list:
        print 'Search text : ' + keyword.search_text

        page = 1
        new_key = None
        new_checked_key = None
        condition = False
        while condition is False:
            response = urllib2.urlopen("https://fr.pornhub.com/video/search?search=" + keyword.search_text + "&o=mr&page=" + str(page))
            page_source = response.read()
            soup = BeautifulSoup(page_source, "html.parser")

            ul = soup.find('ul', class_=regex.compile('videos search-video-thumbs'))
            for li in ul.find_all('li'):
                current = li['_vkey']
                if current == keyword.key:
                    condition = True
                    break
                elif current == keyword.checked_key:
                    condition = True
                    print 'Normal last key not found !'
                    break
                else:
                    a_img = None
                    for img in li.find_all('img'):
                        if img['class'] != "privateOverlay":
                            a_img = img

                    duration = li.find('var', {'class': ['duration']}).text
                    hd = li.find('span', {'class': 'hd-thumbnail'})
                    percent = li.find('div', {'class': 'value'}).text
                    views = li.find('span', {'class': 'views'}).text
                    verified = li.find('span', {'class': 'own-video-thumbnail main-sprite tooltipTrig'})
                    added = li.find('var', {'class': 'added'}).text

                    result_by_keyword[keyword] = {}
                    result_by_keyword[keyword]['TITLE'] = 'no title' if not a_img else a_img['alt']
                    result_by_keyword[keyword]['VIDEO_KEY'] = current
                    result_by_keyword[keyword]['IMAGE'] = 'no pic' if not a_img else a_img['data-mediumthumb']
                    result_by_keyword[keyword]['DURATION'] = duration
                    result_by_keyword[keyword]['QUALITY'] = 'LOW' if not hd else hd.text
                    result_by_keyword[keyword]['VOTE'] = percent
                    result_by_keyword[keyword]['VIEWS'] = views
                    result_by_keyword[keyword]['VERIFIED'] = 'NOT CHECKED' if not verified else 'CHECKED'
                    result_by_keyword[keyword]['TIME'] = added

                    if not new_key: new_key = current
                    if not new_checked_key and verified: new_checked_key = current

            page += 1

        if new_key:
            if not new_checked_key: new_checked_key = keyword.checked_key
            user.update_keyword(keyword.search_text, new_key, new_checked_key)

    html = sample.html_format.create(result_by_keyword)

    with open("file.html", "w") as text_file:
        text_file.write(html)

    webbrowser.open('file://' + os.path.realpath("file.html"))
    user.save()

