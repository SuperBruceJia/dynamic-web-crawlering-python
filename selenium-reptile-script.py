#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Author: Shuyue Jia
@Date: Arg 8, 2020
"""

# import necessary packages
import requests
import time
import numpy as np
import sys
import re
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
import xml
import pandas as pd


def read_url(url: str, driver_path: str):
    """
    Read the website and return the contents of the website
    :param url: The url of the website
    :param driver_path: The path of the Google Chrome Driver
    :return soup.text: The contents of the website
    """
    start_time = time.time()
    option = webdriver.ChromeOptions()
    option.add_argument(
        'user-agent="MQQBrowser/26 Mozilla/5.0 (Linux; U; Android 2.3.7; zh-cn; MB200 Build/GRJ22; CyanogenMod-7) '
        'AppleWebKit/533.1 (KHTML, like Gecko) Version/4.0 Mobile Safari/533.1"')
    option.add_argument(
        'user-agent="Mozilla/5.0 (iPhone; CPU iPhone OS 9_1 like Mac OS X) AppleWebKit/601.1.46 (KHTML, like Gecko) '
        'Version/9.0 Mobile/13B143 Safari/601.1"')

    option.add_argument('--disable-infobars')
    option.add_argument('--incognito')
    option.add_argument('headless')
    option.add_argument("--start-maximized")
    option.add_argument('blink-settings=imagesEnabled=false')

    desired_capabilities = DesiredCapabilities.CHROME
    desired_capabilities["pageLoadStrategy"] = "none"

    prefs = {
        "profile.managed_default_content_settings.images": 2,
        'profile.default_content_settings.popups': 0
    }
    option.add_experimental_option("prefs", prefs)
    # option.add_experimental_option("excludeSwitches", ["ignore-certificate-errors"])

    # PROXY = "proxy_host:proxy:port"
    # desired_capabilities = option.to_capabilities()
    # desired_capabilities['proxy'] = {
    #     "httpProxy": PROXY,
    #     "ftpProxy": PROXY,
    #     "sslProxy": PROXY,
    #     "noProxy": None,
    #     "proxyType": "MANUAL",
    #     "class": "org.openqa.selenium.Proxy",
    #     "autodetect": False
    # }

    # If you don't have Google Chrome Driver installed, uncomment this line
    # driver_path = ChromeDriverManager().install()
    driver = webdriver.Chrome(driver_path, chrome_options=option, desired_capabilities=desired_capabilities)
    # driver.implicitly_wait(0.1)
    driver.get(url)
    contents = driver.page_source

    START = contents.find('serverContent')
    END = contents.find('QRcodebox')
    contents_cut = contents[START:END]
    end_time = time.time()
    print('Time used for get the website was %7f' % (end_time - start_time))
    return contents, contents_cut, driver


def find_English_term(content: str):
    """
    Find the English Term from the contents
    :param content: The contents of the website
    :return Eng_term: The found English term
    :return content: The contents that cut the English term part
    """
    mark = content.find('detail_content')
    temp_cont = content[mark-100:mark]
    START = temp_cont.find('">')
    END = temp_cont.find('</a></h3>')
    Eng_term = temp_cont[START+2:END]
    content = content[mark+len('detail_content'):]
    return Eng_term, content


def find_Chinese_term(content: str):
    """
    Find the Chinese Term from the contents
    :param content: The contents of the website
    :return Chi_term: The found Chinese Term
    :return content: The contents that cut the Chinese term part
    """
    if '中文名称' not in content:
        Chi_term = ''
    else:
        mark = content.find('target')
        temp_cont = content[mark:mark+100]
        START = temp_cont.find('target')
        END = temp_cont.find('</a>')
        Chi_term = temp_cont[START+len('target="_blank">'):END]
        chi_loc = content.find(Chi_term)
        content = content[chi_loc+len(Chi_term):]
    return Chi_term, content


def find_English_definition(content: str):
    """
    Find the English Definition from the content
    :param content: The contents of the website
    :return Eng_def: The found English definition
    :return content: The contents that cut the English definition part
    """
    if '释义' not in content:
        Eng_def = ''
    else:
        START = content.find('释义')
        END = content.find('</i>')
        Eng_def = content[START+len('释义：<span><i>'):END]
        content = content[END+len('</i></span></div>'):]
    return Eng_def, content


def synonym(content: str):
    """
    Find all the Synonym words w.r.t. the English term
    :param content: The contents of the website
    :return synonym_words: The found synonym words
    """
    if '同义词' not in content:
        synonym_words = ''
    else:
        START = content.find('同义词')
        END = content.find('范畴')
        main_content = content[START:END]

        key_word = 'target'
        synonym_words = []
        cur_content = main_content
        while key_word in cur_content:
            start = cur_content.find('target') + len('target')
            ite_content = cur_content[start:start+100]

            new_start = ite_content.find(">")
            end = ite_content.find('</a></span>')
            synonym_word = ite_content[new_start+1:end]
            synonym_words.append(synonym_word)

            cur_content = cur_content[start+1:]

        synonym_words = np.array(synonym_words)
        synonym_words = np.squeeze(synonym_words)
        synonym_words = str(synonym_words).replace('[', '')
        synonym_words = [str(synonym_words).replace(']', '')]

        content = content[END:]
    return synonym_words, content


def field(content: str):
    """
    Find and save all the Fields of this particular term
    :param content: The contents of the website
    :return content: The Fields contents
    """
    if '范畴' not in content:
        field = ''
    else:
        content.replace("title=""", '')
        START = content.find('target') + len('target')
        content = content[START:]

        field = []
        new_content = content
        while 'title' in new_content:
            start = new_content.find('title=') + len('title=')
            end = new_content.find('><span')
            temp_field = new_content[start+1:end-1]
            if temp_field != '':
                field.append(temp_field)

            new_content = new_content[start:]

        field = np.array(field)
        field = np.squeeze(field)
        field = str(field).replace('[', '')
        field = [str(field).replace(']', '')]
    return field


# The main function
if __name__ == "__main__":
    index = 1
    English_terms = []
    Chinese_terms = []
    English_definition = []
    Synonym_words = []
    Fileds_summary = []

    start = '0'
    end = '100w'
    save_file = start + '-' + end

    start_index = int(0)
    end_index = int(1000000)

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

        url = 'https://www.nstl.gov.cn/stkos_detail.html?id=C019' + i
        driver_path = '/Users/shuyuej/.wdm/drivers/chromedriver/mac64/84.0.4147.30/chromedriver'
        save_path = 'NSTD_data/'

        contents, contents_cut, driver = read_url(url=url, driver_path=driver_path)

        if '暂无相关资源' in contents:
            print('There is no data in this webpage! Skip and continue......')
            continue
        else:
            Eng_term, con_cut_eng = find_English_term(content=contents_cut)
            English_terms.append([Eng_term])

            Chi_term, con_cut_chi = find_Chinese_term(content=con_cut_eng)
            Chinese_terms.append([Chi_term])

            Eng_def, con_cut_def = find_English_definition(content=con_cut_chi)
            English_definition.append([Eng_def])

            synonym_word, synonym_cut_con = synonym(content=con_cut_def)
            Synonym_words.append([synonym_word])

            fields = field(content=synonym_cut_con)
            Fileds_summary.append([fields])

            index += 1
            print('It\'s ' + str(i) + ' Website, saved its data, and continue......')

    rows = np.shape(English_terms)[0]
    English_terms = np.reshape(English_terms, [rows, 1])
    Chinese_terms = np.reshape(Chinese_terms, [rows, 1])
    English_definition = np.reshape(English_definition, [rows, 1])
    Synonym_words = np.reshape(Synonym_words, [rows, 1])
    Fileds_summary = np.reshape(Fileds_summary, [rows, 1])

    save_data = np.concatenate([English_terms, Chinese_terms, English_definition, Synonym_words, Fileds_summary], axis=1)
    save_data = pd.DataFrame(save_data)
    save_data.to_csv(save_path + '%s.csv' % save_file, sep=',', index=False, header=['English Term', 'Chinese Term', 'English Definition', 'Synonym', 'Field'])

    driver.close()

    print('Cheers! %s\'s NSTL data (%s terms) has been successfully saved!' % (save_file, str(index)))
    driver.quit()
