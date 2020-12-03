import httplib2
from bs4 import BeautifulSoup, SoupStrainer
import sqlite3
import re
import datetime
from googlesearch import search
import time
import datetime

def find_website(gemeinde):
    query = 'homepage gemeinde ' + gemeinde
    name = search(query)[0]  
    start = name.find('://')
    end = name.find('.de/')
    if (end == -1):
        end = name.find('.org')+1
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
    
def get_landkreis(gemeinde):
    query = 'wikipedia gemeinde deutsch ' + gemeinde
    url = search(query)[0]
    http = httplib2.Http()
    status, response = http.request(url)
    response = remove_html(response)
    start = repr(response).find('Landkreis:')+14
    end = repr(response)[start:].find('\\n\\n\\n')
    return repr(response)[start:start+end]

def get_all_gemeinden():
    conn = sqlite3.connect('gemeinde.db')
    c = conn.cursor()
    c.execute('SELECT name FROM masterdata')
    fetched = c.fetchall()
    result = []
    for f in fetched:
        result.extend(f)
    return result

def update_db_landkreis():
    for gemeinde in get_all_gemeinden():
        landkreis = get_landkreis(gemeinde)
        conn = sqlite3.connect('gemeinde.db')
        c = conn.cursor()
        c.execute('update masterdata set landkreis = ? where name = ?;' , [landkreis, gemeinde])
        conn.commit()
        print(gemeinde, landkreis)
        

def run():
    for gemeinde in get_gemeinden():
        if (not data_point_exists(gemeinde)):
            write_to_db(gemeinde, find_website(gemeinde), datetime.datetime.now())
            print(gemeinde, "added")
        else:
            print(gemeinde, "already in database")
