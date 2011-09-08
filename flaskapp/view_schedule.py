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
from flask import session, request, url_for, redirect, abort, flash

from flaskext.genshi import render_response
from flaskapp.globals import *

from sqlalchemy.orm import joinedload
from sqlalchemy.orm.exc import NoResultFound
from database import db_session as sess
from datamodel import Schedule

@app.route('/view_schedule')
def view_schedule():
	schedule = sess.query(Schedule).one()
	assignments = schedule.assignments
	#app.logger.debug(schedule.assignments)
	#Calculate statistics
	total_cost = sum(map(lambda x: x.cost, assignments))
	avg_cost = total_cost/len(assignments)
	return render_response('view_schedule.html', locals())

