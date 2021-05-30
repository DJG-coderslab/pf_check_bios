#!/usr/bin/python3
# -*- coding: utf-8 -*-

import argparse
import os
import re
import time

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup

class Web(object):
    def __init__(self):
        self.driver = webdriver.Chrome()
        self.driver.get("http://whatsin.***REMOVED***/Pages/HomePage.aspx")
        self.host = 'http://whatsin.***REMOVED***/'
        self.href = ''
        self.hrefs = []
        self.tmp_hrefs = []
        self.projects = set()
        self.new_project = False
        self.pn = ''
        self.updated_pn = set()
        
    def set_out_file(self, file):
        self.out_file = file

    def set_WhatsIn(self, pn):
        '''send PN to WhatsIn, opened page with describe this PN
           result in self.driver'''
        pn = pn
        self.sf = self.driver.find_element_by_id('ctl00_txtPartNumber')
        self.sf.clear()
        self.sf.send_keys(pn)
        self.sf.send_keys(Keys.RETURN)
        time.sleep(3)
        
    def parse_first_page(self, pn):
        '''parse self.driver, set:
           - self.set_href to all models
           - self.project 
           there should be only one valid a href -> to pagw with all models
        '''
        pn = pn
        html = BeautifulSoup(self.driver.page_source, 'lxml')
        all_hrefs = html.find_all('a')
        for a_href in all_hrefs:
            if a_href.has_attr('href'):
                if 'Model' in a_href['href']:
                    self.set_model(a_href['href'])
    
    def set_pn(self, pn):
        '''set global pn'''
        self.pn = pn
        
    def set_model(self, href):
        tmp = re.match(r'^.*=(.+)[ $]', href, flags=0)
        self.model = tmp.group(1)
        self.updated_pn.add('{};{}\n'.format(self.pn, self.model))

    def close_web(self):
        self.driver.close()

    def add_to_file(self):
        pns = self.updated_pn
        data = ''
        f_name = os.path.normpath(self.out_file)
        for line in pns:
            data += line
        try:
            with open(f_name, mode='at', encoding='utf-8') as f:
                f.write(data)
        except IOError as err:
            print('Error while write to file: {}'.format(err))
            
    def one_step(self, pn):
        '''get all pn in one step:
           - from PN get link to all models
           - iter by models to get all pn
           - append result to file
        '''
        pn = pn
        self.set_pn(pn)
        self.set_WhatsIn(pn)
        self.parse_first_page(pn)





parser = argparse.ArgumentParser(prog='ModelUpdater', description='Update model')
parser.add_argument('--in_file', help='file with PN', required=True)
parser.add_argument('--out_file', help='file with PN;model;project', required=True)
args = parser.parse_args()
in_file = os.path.normpath(args.in_file)

print('-'*27)
print('START')
print('-'*27)
web = Web()
web.set_out_file(args.out_file)
tmp = []
try:
    with open(in_file, 'r') as file:
        for pn in file:
            web.one_step(pn.strip())
except Exception as err:
    print(err)
web.add_to_file()

web.close_web()
print('-'*27)
print('THE END')
print('-'*27)