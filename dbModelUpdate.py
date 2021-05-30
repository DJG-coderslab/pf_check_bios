#!/usr/bin/python3
# -*- coding: utf-8 -*-

import argparse
import datetime
import os
import pymysql
import re

server_db = '10.***REMOVED***'
data_base = 'tmp_bios'
data_base = 'BiosChecker'
user_db = 'bios'
pass_db = '***REMOVED***'
connect = pymysql.connect(host=server_db, user=user_db,
                          passwd=pass_db, db=data_base)
cursor = connect.cursor()
nb_pn = 0
nb_models = 0
nb_in_db = []
new_model = 0
updated_pn = 0

def update_db(line):
    '''
       gets one line: pn;model
    '''
    global new_model
    global updated_pn
    file_pn, file_model = line
    sql = '''select pn.PN, m.model, m.id_project   
                from PN as pn inner join model as m inner join project as p 
                on pn.ID_model = m.ID and m.ID_project = p.ID 
                where pn = "{}";'''.format(file_pn)
    cursor.execute(sql)
    connect.commit()
    (db_pn, db_model, db_id_project) = cursor.fetchone()
    sql = '''select m.model from model as m where model = "{}"'''.format(file_model)
    cursor.execute(sql)
    if cursor.fetchone() is None:
        sql = '''insert into model (model, ID_project) values ("{}", "{}")'''.format(file_model, db_id_project)
        cursor.execute(sql)
        connect.commit()
        new_model += 1
    sql = '''select m.id from model as m where model = "{}"'''.format(file_model)
    cursor.execute(sql)
    (db_id_model,) = cursor.fetchone()
    if db_id_model:
        sql = '''UPDATE PN SET ID_model="{}" WHERE PN = "{}"'''.format(db_id_model, file_pn)
        cursor.execute(sql)
        connect.commit()
        updated_pn += 1
        
       




#===============================================================================
#                    START 
#===============================================================================

if __name__ == '__main__':

    parser = argparse.ArgumentParser(prog='dbModelUpdate', 
                                    description='update the models to new format', 
                                    formatter_class=argparse.RawDescriptionHelpFormatter)
    
    parser = argparse.ArgumentParser(prog='WhatsIn2txt', description='Gets models and project based on PN')
    parser.add_argument('--in_file', help='file with PN', required=True)
    args = parser.parse_args()
    in_file = os.path.normpath(args.in_file)
    
    args = parser.parse_args()
    
    file_name = os.path.normpath(args.in_file)
    try:
        with open(file_name, 'r') as file:
            for line in file:
                result = (line.strip().split(';'))
                update_db(result)
    except Exception as err:
        print(err)
        
    print('new models: {}\nupdated pn: {}'.format(new_model, updated_pn))
   
    
    cursor.close()
    connect.close()
    print("END")
