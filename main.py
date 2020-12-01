import httplib2
from bs4 import BeautifulSoup, SoupStrainer
import sqlite3
import re
import datetime
from googlesearch import search
from ipywidgets import IntProgress
from IPython.display import display
import time
import datetime

def find_website(gemeinde):
    conn = sqlite3.connect('gemeinde.db')
    c = conn.cursor()
    c.execute('SELECT link FROM masterdata WHERE name = ?', [gemeinde])
    fetched = c.fetchone()
    return fetched[0]

def is_internal_link(url, link):
    if (url[:4] != 'http'):
        url = 'https://'+url
    if (url in link):
        return link
    elif (link[0] == '/'):
        return url + link
    else:
        return -1

def write_to_db(url, link, payload, its):
    item = [str(url), str(link), str(payload), str(its)]
    conn = sqlite3.connect('gemeinde.db')
    c = conn.cursor()
    c.execute('insert into gemeinde values (?,?,?,?);' , item)
    conn.commit()

def remove_html(text):
    try:
        text = text.decode('utf-8').strip()
    except Exception as e:
        return str(e)      
    result =  re.sub('<[^<]+?>', '', text)      
    return result

def data_point_exists(url, link): 
    item = [str(url), str(link)]
    conn = sqlite3.connect('gemeinde.db')
    c = conn.cursor()
    c.execute('SELECT EXISTS (SELECT 1 FROM gemeinde WHERE url = ? AND link = ?)', item)
    fetched = c.fetchone()
    if (fetched == (1, )):
        return True
    else:
        return False

    
def find_all_links(url):
    https_url = url
    http = httplib2.Http()
    status, response = http.request(https_url)
    
    count = 1
    num_links = len(BeautifulSoup(response, 'html.parser', parse_only=SoupStrainer('a')))
    #print(str(count) + ' von ' + str(num_links) + ': ' + https_url + ' was scraped')
    f = IntProgress(min=0, max=num_links)
    print(url)
    display(f)
    if (not data_point_exists(https_url, https_url)):
        write_to_db(https_url, https_url, remove_html(response), datetime.datetime.now())

    for link in BeautifulSoup(response, 'html.parser', parse_only=SoupStrainer('a')):
        count = count + 1
        f.value += 1
        if (link.has_attr('href') and link['href'] != '' and is_internal_link(url, link['href']) != -1):
            if (not data_point_exists(https_url, is_internal_link(url, link['href']))):
                internal_link = is_internal_link(url, link['href'])
                if (internal_link != -1):
                    status2, response2 =  http.request(internal_link) 
                    write_to_db(https_url, internal_link, remove_html(response2), datetime.datetime.now())
                    #print(str(count) + ' von ' + str(num_links) +  ': ' + internal_link + ' was scraped')

def get_all_gemeinden():
    conn = sqlite3.connect('gemeinde.db')
    c = conn.cursor()
    c.execute('SELECT name FROM masterdata')
    fetched = c.fetchall()
    result = []
    for f in fetched:
        result.extend(f)
    return result

for gemeinde in get_all_gemeinden():
    try:
        find_all_links(find_website(gemeinde))
    except Exception as e:
        write_to_db(gemeinde, 'ERROR in Main ',str(e), datetime.datetime.now())  
               
