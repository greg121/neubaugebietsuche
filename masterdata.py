import httplib2
from bs4 import BeautifulSoup, SoupStrainer
import sqlite3
import re
import datetime
from googlesearch import search
import time
import datetime

def find_website(gemeinde):
    l = []
    query = 'homepage gemeinde ' + gemeinde
    name = search(query)[0]  
    start = name.find('://')
    end = name.find('.de/')
    if (end == -1):
        end = name.find('.org/')+1
    if (end == -1):
        end = name.find('.com/')+1
    if (end == -1):
        end = name.find('.info/')+2
    if (end == -1):
        end = name.find('.eu/')
    result = name[start+3:end+3]
    
    return result

def get_gemeinde(character):
    letters = 'ABCDEFGHIJKLMNOPRSTUVWZ'

    url = 'https://de.wikipedia.org/wiki/Liste_der_St%C3%A4dte_und_Gemeinden_in_Baden-W%C3%BCrttemberg'
    http = httplib2.Http()
    status, response = http.request(url)
    
    response = remove_html(response)
    search_string_start = character + '[Bearbeiten | Quelltext bearbeiten]'
    
    if (character != 'Z'):
        search_string_end = letters[letters.index(character) + 1] + '[Bearbeiten | Quelltext bearbeiten]'
    else:
        search_string_end = 'Gemeindefreie Gebiete[Bearbeiten | Quelltext bearbeiten]'
        #print(response)
    result = response[response.find(search_string_start):response.find(search_string_end)]
    if (character != 'Z'):
        result = repr(result).replace('\\n\\n', '')[39:-74].split("\\n")  
    else:
        result = repr(result).replace('\\n\\n', '')[39:].split("\\n")  
    return result

def remove_html(text):
    try:
        text = text.decode('utf-8').strip()
    except Exception as e:
        return str(e)      
    result =  re.sub('<[^<]+?>', '', text)      
    return result

def get_gemeinden():
    letters = 'ABCDEFGHIJKLMNOPRSTUVWZ'
    letters = list(letters)
    gemeinden = []

    for l in letters:
        temp = get_gemeinde(l)
        gemeinden.extend(temp)
    return gemeinden

def write_to_db(name, link, its):
    item = [str(name), 'https://'+str(link), str(its)]
    conn = sqlite3.connect('gemeinde.db')
    c = conn.cursor()
    c.execute('insert into masterdata values (?,?,?);' , item)
    conn.commit()
    
def data_point_exists(name):
    conn = sqlite3.connect('gemeinde.db')
    c = conn.cursor()
    c.execute("SELECT EXISTS (SELECT 1 FROM masterdata WHERE name = ? and not link = 'https://')", [name])
    fetched = c.fetchone()
    if (fetched == (1, )):
        return True
    else:
        return False
        
for gemeinde in get_gemeinden():
    if (not data_point_exists(gemeinde)):
        write_to_db(gemeinde, find_website(gemeinde), datetime.datetime.now())
        print(gemeinde, "added")
    else:
        print(gemeinde, "already in database")
