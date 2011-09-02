# coding=UTF-8
"""
Administer Course Info
~~~~~~~~~~~~~~~~~~~~~~

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
from datamodel import Course, Pref, TimePref, PrefType

@app.route('/courses')
def list_courses():
	require_auth('admin')
	courses = \
		sess.query(Course).outerjoin(TimePref).outerjoin(Pref).outerjoin(PrefType).all()
	return render_response('list_courses.html',dict(courses=courses))

def get_pref(pref_type, pref_name):

	#memoize, so we don't have to commit at each interval and also minimizes selects
	if (pref_type,pref_name) in get_pref.prefs:
		pref = get_pref.prefs[(pref_type, pref_name)]
		#app.logger.debug('pref %r found in cache' % pref)
		return pref

	try:
		pref = sess.query(Pref).join(PrefType).filter(Pref.name == pref_name).filter(PrefType.name == pref_type).one()
		get_pref.prefs[(pref_type,pref_name)] = pref
		#app.logger.debug('pref %r to found in db' % pref)
		return pref
	except NoResultFound:
		pref = Pref()
		pref_type_id = sess.query(PrefType.pref_type_id).filter(PrefType.name == pref_type).one()
		if pref_type_id is None:
			raise Exception('pref_type %s not found' % pref_type)
		pref.pref_type_id = pref_type_id.pref_type_id
		pref.name = pref_name
		#sess.add(pref)
		#sess.commit()
		get_pref.prefs[(pref_type,pref_name)] = pref

		#app.logger.debug('Adding pref %r to the db' % pref)
		return pref


def get_time(days_bfield, start_time, stop_time):
	id_tuple = (days_bfield, start_time, stop_time)
	
	if start_time == 'WEB':
		if get_time.web_time is not None: return get_time.web_time

		try:
			time = time.sess.query(TimePref).filter_by(time_type='online').one()
		except NoResultFound:
			time = TimePref(time_type='online')
			#sess.add(time)
		get_time.web_time = time
		return time

	if id_tuple in get_time.times:
		time = get_time.times[id_tuple]
		app.logger.debug('found time %r in the cache' % time)
		return time


	days_dict = bfield2dict(days_bfield)
	start_time = timestr2time(str(start_time))
	stop_time = timestr2time(str(stop_time))

	try:
		time = sess.query(TimePref).filter_by(
			time_type='normal',
			start_time=start_time,
			stop_time=stop_time,
			Sa=False, Su=False,
			**days_dict
		).one()

		get_time.times[id_tuple] = time
		app.logger.debug('found time %r in the db' % time)
		return time
	except NoResultFound:
		time = TimePref()
		time.start_time = start_time
		time.stop_time = stop_time
		time.update(Sa=False,Su=False,**days_dict)

		#sess.add(time)
		app.logger.debug('Adding time %r to the db' % time)
		#sess.commit()

		get_time.times[id_tuple] = time
		return time


"""Map weekday name to short name"""
dayl2s=dict(
	MONDAY='M',
	TUESDAY='T',
	WEDNESDAY='W',
	THURSDAY='R',
	FRIDAY='F'
)

"""Map day short name to bitfield name"""
days=dict(
	M=0b10000,
	T=0b01000,
	W=0b00100,
	R=0b00010,
	F=0b00001
)

'''
def excol2in(excol):
  """Exceol Column name (AB) to index"""
  return sum ([ 26**i * (ord(c) - ord('A') + 1) for i, c in enumerate(reversed(excol.upper()))]) - 1
'''

def course2bfield(course):
	"""turn a course dict as per from the CSV into a bitfield
	if a day is "true" then the key of that days long name will be set to it's short name
	e.g. course['WEDNESDAY'] == 'W'
	if it's not then the value will be empty course['WEDNESDAY'] == ''
	"""
	global dayl2s, days

	bfield = 0
	for l,s in dayl2s.items():
		if  (l in course and course[l] == s) or \
			(s in course and course[s] == s):
			bfield |= days[s]

	return bfield

def bfield2dict(bfield):
	"""turn a days of the week bitfield into a dict of short name => boolean true/false"""
	global days
	r = {}
	for k, v in days.items():
		r[k] = (bfield & v) != 0
	return r

def timestr2time(timestr):
	"""convert time in HHMM format to datetime.time object"""
	hours = int(timestr[0:-2])
	mins = int(timestr[-2:])

	return datetime.time(hours,mins)

def clear_course_pref_data():
	"""Delete all Course, Pref, and TimePref Data"""

	sess.query(Course).delete()

	#deleting a child deletes it's parent entry, but deleting a parent doesn't delete the child entry
	for tp in sess.query(TimePref).all():
		sess.delete(tp)
	sess.commit()

	sess.query(Pref).delete()
	sess.commit()

@app.route('/courses/upload', methods=['POST','GET'])
def upload_courses():
	"""Upload Courses from banweb dump, "folding" mentored inquiries for each course into the course"""
	require_auth('admin')

	if request.method == 'POST':
		reset_memo_cache()

		reader = csv.DictReader(request.files['courses_file'])
		courses = {} #row of tuples, first value contains a master row
		             #second value contains list of Mentored Inqueries

		clear_course_pref_data()

		#1st pass group MENTORED INQUIRY with main course
		for row in reader:
			if 'MENTORED INQUIRY' in row['CATALOG TITLE'] or 'MENT INQ' in row['CATALOG TITLE']:
				#attach mentored inquiry to assoc. course
				course_no = row['COURSE NO']

				#decrease ascii value of final character by one
				#to turn for example 101B into 101A
				rel_course = course_no[0:-1] + chr(ord(course_no[-1]) - 1)
				if rel_course not in courses:
					#Courses may be out of order, so 101B might come before 101A
					courses[rel_course] = (None, [row])
				else:
					courses[rel_course][1].append(row)
			else:
				courses[row['COURSE NO']] = (row, [])

		#2nd pass turn the grouped courses into a single SQLAlchemy object
		for master_course, inquiries in courses.values():
			course = Course()

			course.crn = master_course['CRN']
			course.prefs = []

			#handle faculty pref
			faculty_name = master_course['INSTR LAST NAME'] + ', ' + master_course['INSTR FIRST NAME']

			faculty_pref = get_pref('Faculty', faculty_name)

			course.prefs.append(faculty_pref)

			#theme pref
			theme_pref = get_pref('Theme', master_course['CATALOG TITLE'])
			course.prefs.append(theme_pref)

			#time pref
			all_courses = inquiries + [ master_course ]
			days_bfield = reduce(operator.or_, map(course2bfield, all_courses))

			start_time = min([int(c['BEGIN TIME']) for c in all_courses])
			stop_time  = max([int(c[  'END TIME']) for c in all_courses])

			course.time = get_time(days_bfield,start_time,stop_time)
			course.prefs.append(course.time)

			sess.add(course)

		sess.commit()

		return redirect(url_for('list_courses'))
	else:
		#display form
		return render_response('upload_courses.html')

def get_time_by_obj(time_obj):
	if time_obj.name in get_time_by_obj.times:
		return get_time_by_obj.times[time_obj.name]

	try:
		time = sess.query(TimePref).filter_by(name=time_obj.name).one()
	except NoResultFound:
		time = time_obj

	get_time_by_obj.times[time.name] = time
	return time

def reset_memo_cache():
	"""reset the memoization cache for various get_* functions"""
	get_pref.prefs = {}
	get_time.times = {}
	get_time.web_time = None
	get_time_by_obj.times = {}

@app.route('/courses/upload_flat', methods=['GET','POST'])
def upload_courses_flat():
	"""Upload "flat" courses file, one row per course"""
	require_auth('admin')

	if request.method == 'POST':
		reset_memo_cache()
		clear_course_pref_data()

		errors = []

		reader = csv.DictReader(request.files['courses_file'])
		for row in reader:
			course = Course()
			course.crn = row['CRN']
			if not course.crn:
				errors.append('Course missing a CRN, row=%r' % row)

			## Theme ##
			theme_name = row['Theme']
			#clean theme name, for example turn "GLOBAL PERSPECTIVES: EUROPE" into simply "GLOBAL PERSPECTIVES"
			if ': ' in theme_name:
				theme_name = theme_name.rsplit(': ')[0]

			theme_name = theme_name.strip()

			if not theme_name:
				errors.append('Theme name missing for course with CRN %s' % course.crn)
			else:
				course.prefs.append( get_pref('Theme', theme_name) )

			## Faculty ##
			faculty_name = ''
			last_name = row['Faculty Last Name'].strip()
			first_name = row['Faculty First Name'].strip()
			if first_name and last_name:
				faculty_name = last_name + ', ' + first_name
			elif last_name or first_name:
				faculty_name = last_name or first_name

			if faculty_name:
				course.prefs.append( get_pref('Faculty', faculty_name) )
			else:
				errors.append('Both first and last faculty name for course with CRN %s is empty' % course.crn)

			## Time ##
			time = TimePref()
			time_name = row['Corresponding Time']
			if time.parse_name(time_name):
				time = get_time_by_obj(time)
				course.time = time
				course.prefs.append(course.time)
			else:
				errors.append('Time with name %s not parseable, must be in format, MTWRF 000-2459 with optional trailing' % time_name)

			if 'Assigned Mentor' in row and row['Assigned Mentor'].strip():
				course.pre_assn_mentor_odin = row['Assigned Mentor'].strip()
			sess.add(course)

		#all missing errors
		app.logger.debug('Course Upload Errors: %r' % errors)

		sess.commit()

		return redirect(url_for('list_courses'))
	else:
		return render_response('upload_courses_flat.html')
