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

class wait_for_page_load(object):

    def __init__(self, browser):
        self.browser = browser

    def __enter__(self):
        self.old_page = self.browser.find_element_by_tag_name('html')

    def page_has_loaded(self):
        new_page = self.browser.find_element_by_tag_name('html')
        return new_page.id != self.old_page.id

    #def __exit__(self, *_):
    #    wait_for(self.page_has_loaded)


class Web(object):
    def __init__(self, param):
        self.driver = webdriver.Chrome()
        self.driver.get("http://whatsin.***REMOVED***/Pages/HomePage.aspx")
        self.host = 'http://whatsin.***REMOVED***/'
        self.href = ''
        self.hrefs = []
        self.tmp_hrefs = []
        self.projects = set()
        self.new_project = False
        self.pn = ''
        self.debug = param
        self.is_know_pn = False
        
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
        time.sleep(5)
        
    def get_pn(self, pn):
        '''parse opened page and in result[] there are [model, project]'''
        pn = pn
        result = []
        self.debug.add_info('get_pn {}'.format(pn))
        for a in self.driver.find_elements_by_xpath('.//a'):
            if a.get_attribute('href') is not None:
                if 'Model' in a.get_attribute('href'):
                    tmp = re.match(r'^.*=([\w-]+).*$',a.get_attribute('href'),flags=0)
                    result.append(tmp.group(1), pn)
                if 'Project' in a.get_attribute('href'):
                    tmp = re.match(r'^.*=(.+)$',a.get_attribute('href'),flags=0) 
                    result.append(tmp.group(1))
        return result
    
    def parse_first_page(self, pn):
        '''parse self.driver, set:
           - self.set_href to all models
           - self.project 
           there should be only one valid a href -> to page with all models
        '''
        self.debug.add_info('\tparse_firs_page {}'.format(pn))
        pn = pn
        html = BeautifulSoup(self.driver.page_source, 'lxml')
        all_hrefs = html.find_all('a')
        for a_href in all_hrefs:
            if a_href.has_attr('href'):
                self.is_know_pn = True
                if 'Project' in a_href['href']:
                    tmp = '{}{}{}'.format(self.host, 'Pages/', a_href['href'])
                    self.set_href(tmp)
                    self.set_project(tmp)
                elif 'Model' in a_href['href']:
                    self.set_model(a_href['href'])
                else:
                    self.is_know_pn = False
    
    def set_href(self, href):
        '''in self.href is link with project'''
        self.href = href
        
    def set_pn(self, pn):
        '''set global pn'''
        self.pn = pn
        
    def set_project(self, href):
        self.debug.add_info('\tset_project {}'.format(href))
        tmp = re.match(r'http.*=(.+)$', href, flags=0)
        self.project = tmp.group(1)
        self.new_project = False
        if not self.project in self.projects:
            self.projects.add(self.project)
            self.new_project = True
        print('\t{}'.format(self.project))

    def are_models(self):
        '''check if there are any models
           call the page from href with ...?Project=
           get the table with all models or 0 Result
           
           return:
           True - there are models
           False - no models in table
        '''
        models = False
        self.driver.get(self.href)
        html = BeautifulSoup(self.driver.page_source, 'lxml')
        for string in html.find(id='ctl00_MainContent_CountLabel').strings:
            if re.match(r'^[1-9]+ Results Found', string, flags=0):
                models = True
        return models
    
    def get_xls(self):
        '''
            gets the xml file with all PN
        '''
        if self.are_models():
            import urllib.request
            url = '{}{}'.format(self.host, 'Pages/ExcelExport_Project.aspx', self.project)
            file_name = os.path.normpath('y:/plik.xls')
            urllib.request.urlretrieve(url, file_name)
    
    def search_models(self):           
        '''
            write to file all pn for given PN  
        '''
        pns = set()
        self.debug.add_info('\tsearch_models')
        if self.are_models():
            self.debug.add_info('\t\tare_models')
            models = set()
            html = BeautifulSoup(self.driver.page_source, 'lxml')
            table = html.find(id='ctl00_MainContent_ProjectGridView')
            t_body = table.find('tbody')
            rows = t_body.find_all('tr')
            for row in rows:
                cells = row.find_all('td')
                if len(cells) > 1:
                    href = '{}{}{}'.format(self.host, 'Pages/', cells[3].a['href'])
                    self.debug.add_info('\t\t{}'.format(href))
                    if not href in models:
                        models.add(href)
                        if self.are_pns(href):
                            self.driver.find_element_by_id('ctl00_MainContent_ShowallCheckbox').click()
                            time.sleep(5)
                            pns.update(self.parse_pns_table())
                            self.debug.add_info('\t\t{}'.format(self.parse_pns_table()))
                        else:
                            pns.add('{};{};{}\n'.format(self.pn, self.model, self.project))
        else:
            pns.add('{};{};{}\n'.format(self.pn, self.model, self.project))
        if not self.pn in pns:
            '''
            sometimes given pn not exist in table of all pn
            '''
            pns.add('{};{};{}\n'.format(self.pn, self.model, self.project))
        if pns:
            self.add_to_file((pns))
            
    def are_pns(self, href):
        '''
            check if in href http://...?Model= there are any PNs 
        '''
        href = href
        pns = False
        self.driver.get(href)
        html = BeautifulSoup(self.driver.page_source, 'lxml')
        for string in html.find(id='ctl00_MainContent_CountLabel').strings:
            if re.match(r'^[1-9]\d* Result.?s.? Found', string, flags=0):
                pns = True
        return pns
    
    def parse_pns_table(self):
        '''
            goes through the table with all PN
            
            out: set(pn, model, project)
        '''
        self.debug.add_info('\tparse_pns_table')
        pns = set()
        page = self.driver.page_source
        html = BeautifulSoup(page, 'lxml')
        table = html.find(id='ctl00_MainContent_NBGridView')
        t_body = table.find('tbody')
        rows = t_body.find_all('tr')
        for row in rows:
            cols = row.find_all('td')
            if len(cols)>7:
                if 'EMEA' in cols[7].string:
                    pn = cols[0].string
                    model = cols[1].string 
                    project = cols[2].string
                    pns.add('{};{};{}\n'.format(pn, model, project))
        return pns
        
        
    def get_all_pn(self):
        '''
            function gets all pn for project from pn
        '''
        self.search_models()

    def set_model(self, href):
        self.debug.add_info('\tset_model {}'.format(href))
        tmp = re.match(r'^.*=(.+)[ $]', href, flags=0)
        self.model = tmp.group(1)

    def close_web(self):
        self.driver.close()

    def add_to_file(self, pns):
        pns = pns
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
        self.debug.add_info('PN: {}'.format(pn))
        pn = pn
        self.set_pn(pn)
        self.set_WhatsIn(pn)
        self.parse_first_page(pn)
        if self.is_know_pn:
            if self.new_project:
                self.get_all_pn()
            else:
                pns = set()
                pns.add('{};{};{}\n'.format(self.pn, self.model, self.project))
                self.add_to_file((pns))
        
        
        

class Insterface():
    pass

class Debug(object):
    def __init__(self):
        self.info = []
        
    def add_info(self, info):
        self.info.append(info)
        
    def show(self):
        print('='*37)
        print('DEBUG')
        print('='*37)
        for info in self.info:
            print('{}'.format(info))

parser = argparse.ArgumentParser(prog='WhatsIn2txt', description='Gest models and project based on PN')
parser.add_argument('--in_file', help='file with PN', required=True)
parser.add_argument('--out_file', help='file with PN;model;project', required=True)
parser.add_argument('-d', '--debug', action='store_true', help='debug output', required=False)
args = parser.parse_args()
in_file = os.path.normpath(args.in_file)

print('-'*27)
print('START')
print('-'*27)

deb = Debug()
web = Web(deb)
web.set_out_file(args.out_file)
tmp = []
try:
    with open(in_file, 'r') as file:
        for pn in file:
            web.one_step(pn.strip())
except Exception as err:
    print(err)

web.close_web()
print('-'*27)
print('THE END')
print('-'*27)

if args.debug:
    deb.show()