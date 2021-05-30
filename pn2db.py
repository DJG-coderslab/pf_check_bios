#!/usr/bin/python3
# -*- coding: utf-8 -*-

import argparse
import datetime
import os
import pymysql
import re
	
'''
skrypt do importowania brakujących PN, model i projekt
dane wejściowe powinny byc w formacie:
- w jednej linii jewna wartośc
- poszczególne pola oddzielone średnikiem
- pn;model;project
'''

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

def check_db(sql):
	result = False
	try:
		cursor.execute(sql)
		connect.commit()
		if cursor.fetchone() is not None:
			result = True
	except Exception as err:
		print(err)
	return result		

def is_project_db(project):
	sql = '''select project from project where project = "{}"'''.format(project)
	return check_db(sql)

def is_model_db(model):
	sql = ''' select model from model where model = "{}"'''.format(model)
	return check_db(sql)
	
def is_pn_db(pn):
	sql = '''select PN from PN where PN = "{}"'''.format(pn)
	return check_db(sql)

def pn2db(model, pn):
	sql = '''select ID from model where model = "{}"'''.format(model)
	try:
		cursor.execute(sql)
		connect.commit()
		_id = cursor.fetchone()
		if _id is not None:
			sql = '''insert into PN (PN, ID_model) values ("{}", "{}")'''.format(pn, _id[0])
			cursor.execute(sql)
			connect.commit()
	except Exception as err:
		print(err)
	
def model2db(project, model, pn):
	result = False
	sql = '''select ID from project where project = "{}"'''.format(project)
	try:
		cursor.execute(sql)
		_id = cursor.fetchall()
		if len(_id) > 1:
			''' jeśli jest więcej niz jeden wiersz z danym projektem'''
			print('{} ma {} wersje, PN: {}, M: {}'.format(project, len(_id), pn, model))
		else:
			sql = '''insert into model (model, ID_project) values ("{}", "{}")'''.format(model, _id[0][0])
			cursor.execute(sql)
			connect.commit()
			result = True
	except Exception as err:
		print(err)
	return result

def add2db(line):
	global nb_pn, nb_models, nb_in_db
	pn_f, model_f, project_f = line
	if is_model_db(model_f):
		if is_pn_db(pn_f):
			nb_in_db.append(pn_f)
		else:
			pn2db(model_f, pn_f)
			nb_pn += 1
	else:
		if is_project_db(project_f):
			if model2db(project_f, model_f, pn_f):
				nb_models += 1
				if is_pn_db(pn_f):
					nb_in_db.append(pn_f)
				else:
					pn2db(model_f, pn_f)
					nb_pn += 1
		else:
			'''nie ma projektu w bazie'''
			sql = '''select ID from model where model = "{}"'''.format(model_f)
			cursor.execute(sql)
			connect.commit()
			_id = cursor.fetchone()
			if _id is None:
				'''model nie wystepuje w bazie'''
				print ("{} nie ma w bazie; PN: {}, Model: {}".format(project_f, pn_f, model_f))
			else:
				print ("{} nie ma w bazie; PN: {}, M: {} (id: {})".format(project_f, pn_f, model_f, _id[0]))
				sql = '''select id, project from project where project like "{}%"'''.format(project_f)
				cursor.execute(sql)
				connect.commit()
				for _project_f_db in cursor.fetchall():
					print(_project_f_db)

def diagnostic_out(module):
	global nb_pn, nb_models, nb_in_db
	if module == 'input':
		print ("Dodane: {} modeli i {} pn".format(nb_models, nb_pn))
		if nb_in_db:
			print('{} pn pominiętych, już są w bazie'.format(len(nb_in_db)))
	pass

def add_pn(args):
	file_name = os.path.normpath(args.file)
	try:
		with open(file_name, 'r') as file:
			for line in file:
				result = (line.strip().split(';'))
				add2db(result)
	except Exception as err:
		print(err)
	diagnostic_out('input')
		
def get_new_pn(args):
	file_name = os.path.normpath(args.file)
	sql = '''select distinct SerialNumber from tmp order by SerialNumber'''
	try:
		if os.path.isfile(file_name):
			os.remove(file_name)
		with open(file_name, 'a') as out:
			cursor.execute(sql)
			connect.commit()
			for item in cursor.fetchall():
				print('{}'.format(item[0]))
				out.write('{}\n'.format(item[0]))
				sql = '''delete from tmp where SerialNumber = "{}"'''.format(item[0])
				cursor.execute(sql)
				connect.commit()
	except Exception as err:
		print(err)

def add_project(args):
	bios = args.bios
	project = args.project
	if args.date is None:
		t_stamp = '{:%Y-%m-%d}'.format(datetime.datetime.now())
	else:
		t_stamp = args.date
	sql = '''insert into project (project, bios_version, date) values ("{}","{}","{}")'''.format(project, bios, t_stamp)
	cursor.execute(sql)
	connect.commit()

#===============================================================================
#					START 
#===============================================================================

if __name__ == '__main__':

	parser = argparse.ArgumentParser(prog='pn2db', 
									description='PN to DB for Checker Bios', 
									formatter_class=argparse.RawDescriptionHelpFormatter)
	subparsers = parser.add_subparsers(help='commands')
	
	getpn_parser = subparsers.add_parser('get_pn', help='Get the new PNs from DB')
	getpn_parser.add_argument('-f', '--file', help='File to write PNs', required=True)
	getpn_parser.set_defaults(func=get_new_pn)
	
	addpn_parser = subparsers.add_parser('add_pn', help='Add the new PNs, models to DB')
	addpn_parser.add_argument('-f', '--file', help='File with PNs', required=True)
	addpn_parser.set_defaults(func=add_pn)
	
	addprj_parser = subparsers.add_parser('add_project', help='Add the new project to DB')
	addprj_parser.add_argument('-p', '--project', help='Name of project', required=True)
	addprj_parser.add_argument('-b', '--bios', help='Version of BIOS', required=True)
	addprj_parser.add_argument('-d', '--date', help='Valid from date', required=False)
	addprj_parser.set_defaults(func=add_project)
	
	args = parser.parse_args()
	if hasattr(args, 'func'):
		args.func(args)
	
	
	cursor.close()
	connect.close()
	print("END")
