# coding=UTF-8
"""
View The Schedule
~~~~~~~~~~~~~~~~~

:Copyright © 2011 Mark Harviston <infinull@gmail.com>

 * Display course information in a convenient spreadsheet-like format
 * Upload a CSV formatted banweb style and upload it
 * TODO make PrefType proof

"""

import csv, operator, datetime

import flask
from flask import session, request, url_for, redirect, abort, flash, make_response, send_file

from flaskext.genshi import render_response
from flaskapp.globals import *

from sqlalchemy.orm import joinedload
from sqlalchemy.orm.exc import NoResultFound
from database import db_session as sess
from datamodel import Schedule
from StringIO import StringIO

@app.route('/view_schedule')
def view_schedule():
	schedule = sess.query(Schedule).one()
	assignments = schedule.assignments

	#Calculate statistics
	total_cost = sum(map(lambda x: x.cost, assignments))
	avg_cost = total_cost/len(assignments)

	return render_response('view_schedule.html', locals())

@app.route('/schedule.csv')
def view_schedule_as_csv():
	#TODO not sure if this is the best way to do it, seems like the output buffer could be opened directly, or something
	w_file = StringIO()
	gen_csv(w_file)
	w_file.seek(0) #rewind to beginning
	return send_file(w_file, 'text/csv', as_attachment=False, attachment_filename='schedule.csv')
	#return send_file(w_file, 'text/plain')

def gen_csv(w_file):
	schedule = sess.query(Schedule).one()
	assignments = schedule.assignments

	#Calculate statistics
	total_cost = sum(map(lambda x: x.cost, assignments))
	avg_cost = total_cost/len(assignments)

	writer = csv.writer(w_file)
	writer.writerow(('CRN','Time','Theme','Faculty','Mentor'))
	for assn in assignments:
		prefs = assn.course.prefs_as_dict()
		writer.writerow((
			assn.course.crn,
			prefs['Time'],
			prefs['Theme'],
			prefs['Faculty'],
			assn.mentor.full_name
		))

	writer.writerow([])
	writer.writerow(('Total Cost', total_cost))
	writer.writerow(('Average Cost', avg_cost))
