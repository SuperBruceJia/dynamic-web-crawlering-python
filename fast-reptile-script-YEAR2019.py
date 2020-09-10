#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Author: Shuyue Jia
@Date: Arg 10, 2020
"""

# Import necessary packages
import os
import ssl
import json
import time
import requests
import numpy as np
import pandas as pd
from urllib import request
from bs4 import BeautifulSoup
from random import randint
import urllib3
import threading

# Disable all kinds of warnings
urllib3.disable_warnings()

# Avoid SSL Certificate to access the HTTP website
ssl._create_default_https_context = ssl._create_unverified_context


def read_url(ID: str) -> str:
    """
    Read the website and return the contents of the website
    :param ID: The ID of the website
    :return soup.text: The contents of the website
    """
    # URL of the website + ID for every word website
    url = 'https://www.nstl.gov.cn/execute?target=nstl4.search4&function=paper/pc/detail&id=C019' + ID

    # A fake device to avoid the Anti reptile
    USER_AGENTS = [
        "Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1; AcooBrowser; .NET CLR 1.1.4322; .NET CLR 2.0.50727)",
        "Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.0; Acoo Browser; SLCC1; .NET CLR 2.0.50727; Media Center PC 5.0; .NET CLR 3.0.04506)",
        "Mozilla/4.0 (compatible; MSIE 7.0; AOL 9.5; AOLBuild 4337.35; Windows NT 5.1; .NET CLR 1.1.4322; .NET CLR 2.0.50727)",
        "Mozilla/5.0 (Windows; U; MSIE 9.0; Windows NT 9.0; en-US)",
        "Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; Win64; x64; Trident/5.0; .NET CLR 3.5.30729; .NET CLR 3.0.30729; .NET CLR 2.0.50727; Media Center PC 6.0)",
        "Mozilla/5.0 (compatible; MSIE 8.0; Windows NT 6.0; Trident/4.0; WOW64; Trident/4.0; SLCC2; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729; .NET CLR 1.0.3705; .NET CLR 1.1.4322)",
        "Mozilla/4.0 (compatible; MSIE 7.0b; Windows NT 5.2; .NET CLR 1.1.4322; .NET CLR 2.0.50727; InfoPath.2; .NET CLR 3.0.04506.30)",
        "Mozilla/5.0 (Windows; U; Windows NT 5.1; zh-CN) AppleWebKit/523.15 (KHTML, like Gecko, Safari/419.3) Arora/0.3 (Change: 287 c9dfb30)",
        "Mozilla/5.0 (X11; U; Linux; en-US) AppleWebKit/527+ (KHTML, like Gecko, Safari/419.3) Arora/0.6",
        "Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.8.1.2pre) Gecko/20070215 K-Ninja/2.1.1",
        "Mozilla/5.0 (Windows; U; Windows NT 5.1; zh-CN; rv:1.9) Gecko/20080705 Firefox/3.0 Kapiko/3.0",
        "Mozilla/5.0 (X11; Linux i686; U;) Gecko/20070322 Kazehakase/0.4.5",
        "Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.8) Gecko Fedora/1.9.0.8-1.fc10 Kazehakase/0.5.6",
        "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/535.11 (KHTML, like Gecko) Chrome/17.0.963.56 Safari/535.11",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_7_3) AppleWebKit/535.20 (KHTML, like Gecko) Chrome/19.0.1036.7 Safari/535.20",
        "Opera/9.80 (Macintosh; Intel Mac OS X 10.6.8; U; fr) Presto/2.9.168 Version/11.52",
    ]

    random_agent = USER_AGENTS[randint(0, len(USER_AGENTS) - 1)]
    headers = {
        'User-Agent': random_agent,
    }

    for j in range(10):
        try:
            res = requests.get(url, headers=headers,
                               verify=False, timeout=(5, 10))
            contents = res.text
        except Exception as e:
            if j >= 9:
                print('The exception has happened', '-' * 100)
            else:
                time.sleep(0.5)
        else:
            time.sleep(0.5)
            break
    return contents


def find_English_term(content: str):
    """
    Find the English Term from the contents
    :param content: The contents of the website
    :return Eng_term: The found English term
    :return content: The contents that cut the English term part
    """
    mark = content.find('范畴号') + len('范畴号')
    temp_cont = content[mark:mark + 100]

    # START and END of the English term
    START = temp_cont.find('["')
    END = temp_cont.find('"]')
    Eng_term = temp_cont[START + 2:END]

    # Cut the English term part from the contents
    content = content[content.find('名称') + len('名称'):]
    return Eng_term, content


def find_Chinese_term(content: str):
    """
    Find the Chinese Term from the contents
    :param content: The contents of the website
    :return Chi_term: The found Chinese Term
    :return content: The contents that cut the Chinese term part
    """
    # If there is no Chinese Term available, then continue
    if '中文名称' not in content:
        Chi_term = ''
    else:
        # START and END of the Chinese Term
        START = content.find('["') + len('["')
        END = content.find('中文名称') - len('"],"n":"')
        Chi_term = content[START:END]

        # Cut the Chinese term part from the contents
        content = content[content.find('中文名称') + len('中文名称'):]
    return Chi_term, content


def find_English_definition(content: str):
    """
    Find the English Definition from the content
    :param content: The contents of the website
    :return Eng_def: The found English definition
    :return content: The contents that cut the English definition part
    """
    # If there is no English definition available, then continue
    if '释义' not in content:
        Eng_def = ''
    else:
        # START and END of the English Definition
        START = content.find('"f":"def","v"') + len('"f":"def","v":["')
        END = content.find('释义')
        Eng_def = content[START:END - len('"],"n":"')]

        # Cut the English Definition part from the contents
        content = content[END + len('释义'):]
    return Eng_def, content


def synonym(content: str):
    """
    Find all the Synonym words w.r.t. the English term
    :param content: The contents of the website
    :return synonym_words: The found synonym words
    """
    # If there is no Synonym Words available, then continue
    if '同义词' not in content:
        synonym_words = ''
    else:
        # Find the Synonym words' mark from the content
        mark = content.find('linkToBaTeleva') + len('linkToBaTeleva')
        new_content = content[mark:]

        # START and END of the Synonym words
        START = new_content.find('["') + len('[')
        END = new_content.find('名称') - len('],"n":"')
        synonym_words = new_content[START:END]
    return synonym_words


def field(ID: str):
    """
    Find and save all the Fields of this particular term
    :param ID: The ID of a particular website (word)
    :return content: The Fields contents
    """
    # URL of the Fields contents
    url = 'https://www.nstl.gov.cn/execute?target=nstl4.search4&function=stkos/pc/detail/ztree&id=C019' + ID

    # A fake device to avoid the Anti reptile
    USER_AGENTS = [
        "Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1; AcooBrowser; .NET CLR 1.1.4322; .NET CLR 2.0.50727)",
        "Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.0; Acoo Browser; SLCC1; .NET CLR 2.0.50727; Media Center PC 5.0; .NET CLR 3.0.04506)",
        "Mozilla/4.0 (compatible; MSIE 7.0; AOL 9.5; AOLBuild 4337.35; Windows NT 5.1; .NET CLR 1.1.4322; .NET CLR 2.0.50727)",
        "Mozilla/5.0 (Windows; U; MSIE 9.0; Windows NT 9.0; en-US)",
        "Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; Win64; x64; Trident/5.0; .NET CLR 3.5.30729; .NET CLR 3.0.30729; .NET CLR 2.0.50727; Media Center PC 6.0)",
        "Mozilla/5.0 (compatible; MSIE 8.0; Windows NT 6.0; Trident/4.0; WOW64; Trident/4.0; SLCC2; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729; .NET CLR 1.0.3705; .NET CLR 1.1.4322)",
        "Mozilla/4.0 (compatible; MSIE 7.0b; Windows NT 5.2; .NET CLR 1.1.4322; .NET CLR 2.0.50727; InfoPath.2; .NET CLR 3.0.04506.30)",
        "Mozilla/5.0 (Windows; U; Windows NT 5.1; zh-CN) AppleWebKit/523.15 (KHTML, like Gecko, Safari/419.3) Arora/0.3 (Change: 287 c9dfb30)",
        "Mozilla/5.0 (X11; U; Linux; en-US) AppleWebKit/527+ (KHTML, like Gecko, Safari/419.3) Arora/0.6",
        "Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.8.1.2pre) Gecko/20070215 K-Ninja/2.1.1",
        "Mozilla/5.0 (Windows; U; Windows NT 5.1; zh-CN; rv:1.9) Gecko/20080705 Firefox/3.0 Kapiko/3.0",
        "Mozilla/5.0 (X11; Linux i686; U;) Gecko/20070322 Kazehakase/0.4.5",
        "Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.8) Gecko Fedora/1.9.0.8-1.fc10 Kazehakase/0.5.6",
        "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/535.11 (KHTML, like Gecko) Chrome/17.0.963.56 Safari/535.11",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_7_3) AppleWebKit/535.20 (KHTML, like Gecko) Chrome/19.0.1036.7 Safari/535.20",
        "Opera/9.80 (Macintosh; Intel Mac OS X 10.6.8; U; fr) Presto/2.9.168 Version/11.52",
    ]

    random_agent = USER_AGENTS[randint(0, len(USER_AGENTS) - 1)]
    headers = {
        'User-Agent': random_agent,
    }

    for j in range(10):
        try:
            res = requests.get(url, headers=headers,
                               verify=False, timeout=(5, 10))
        except Exception as e:
            if j >= 9:
                print('The exception has happened', '-' * 100)
            else:
                time.sleep(0.5)
        else:
            time.sleep(0.1)
            break

    content = res.text

    # Remove some useless contents from the Fields contents
    # e.g., "total":1,"code":0,
    # ,"value":"180911","font":{"color":"#999"}}
    START = content.find('code') + len('code":0,')
    content = content[START:]
    content = content.replace(',"font":{"color":"#999"}', '')
    content = content.replace('"data"', '"Fields"')

    while '"value"' in content:
        mark = content.find('"value"')
        temp_cont = content[mark:mark + 100]
        end = temp_cont.find('"}')

        true_start = mark - 1
        true_end = mark + end + 1

        content = content.replace(content[true_start:true_end], '')
    return content


class MyEncoder(json.JSONEncoder):
    """
    Used to save the numpy array into JSON file
    """

    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        else:
            return super(MyEncoder, self).default(obj)


def save_json(saved_data: list, save_name: str):
    '''
    Save the data (np.array) into JSON file
    :param saved_data: the dataset which should be saved
    :param save_name: the saved path of the JSON file
    :return: saved file
    '''
    file = open(save_name, 'w', encoding='utf-8')
    json.dump(saved_data, file, ensure_ascii=False, indent=4, cls=MyEncoder)
    file.close()


def run_code(start_index: int, end_index: int):
    """
    Run Codes for using multiple threads
    :param start_page: The start page ID
    :param end_page: The end page ID
    """
    JSON_file = ''
    
    for i in range(start_index, end_index):
        if i < 10:
            i = '00000' + str(i)
        elif 10 <= i < 100:
            i = '0000' + str(i)
        elif 100 <= i < 1000:
            i = '000' + str(i)
        elif 1000 <= i < 10000:
            i = '00' + str(i)
        elif 10000 <= i < 100000:
            i = '0' + str(i)
        else:
            i = str(i)

        # Get the contents of the website
        contents = read_url(ID=i)
        # If there is nothing in this website, then skip and continue
        if 'linkToCaClnotn' not in contents:
            print('There is no data in this webpage! Skip and continue......')
            continue
        else:
            # Find the English Term from the contents
            Eng_term, con_cut_eng = find_English_term(content=contents)

            # Find the Chinese Term from the contents
            Chi_term, con_cut_chi = find_Chinese_term(content=con_cut_eng)

            # Find the English Definition from the contents
            Eng_def, con_cut_def = find_English_definition(content=con_cut_chi)

            # Find the Synonym Words from the contents
            synonym_word = synonym(content=con_cut_chi)

            # Find the Fields from another contents
            field_names = field(ID=i)

            # Combine all the found data and make string for JSON
            JSON_file += '{'
            JSON_file += '"English Term": ["'
            JSON_file += Eng_term
            JSON_file += '"], '
            JSON_file += '"Chinese Term": ["'
            JSON_file += Chi_term
            JSON_file += '"], '
            JSON_file += '"English Definition": ["'
            JSON_file += Eng_def
            JSON_file += '"], '
            JSON_file += '"Synonym Words": ['
            JSON_file += synonym_word
            JSON_file += '], '
            JSON_file += field_names

            # Save the JSON File for each word
            save_json(eval(JSON_file), save_path + '%s_word.json' % i)
            print('The %s word JSON file has been successfully saved!' % i)


# The main function
if __name__ == '__main__':
    # The saved path for the JSON and Excel files
    save_path = 'NSTD-data-2019/'
    if not os.path.exists(save_path):
        os.mkdir(save_path)

    threadl = []
    task1 = threading.Thread(target=run_code, args=(0, 50000))
    task2 = threading.Thread(target=run_code, args=(50000, 100000))
    task3 = threading.Thread(target=run_code, args=(100000, 150000))
    task4 = threading.Thread(target=run_code, args=(150000, 200000))
    task5 = threading.Thread(target=run_code, args=(200000, 250000))
    task6 = threading.Thread(target=run_code, args=(250000, 300000))
    task7 = threading.Thread(target=run_code, args=(300000, 350000))
    task8 = threading.Thread(target=run_code, args=(350000, 400000))
    task9 = threading.Thread(target=run_code, args=(400000, 450000))

    task1.start()
    task2.start()
    task3.start()
    task4.start()
    task5.start()
    task6.start()
    task7.start()
    task8.start()
    task9.start()
