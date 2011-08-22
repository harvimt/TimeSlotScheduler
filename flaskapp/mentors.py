# coding=UTF-8
"""
Administrate Mentors
~~~~~~~~~~~~~~~~~~~~

:Copyright © 2011 Mark Harviston <infinull@gmail.com>

 * Display the list of mentors
 * Upload a CSV formatted qualtrics style and load the data
 * TODO make PrefType proof

"""

import csv, datetime

import flask
from flask import session, request, url_for, redirect, abort, flash

from flaskext.genshi import render_response
from flaskapp.globals import *

from flatland import Form, String, Constrained, Enum
from flatland.validation import NoLongerThan
from flatland.out.genshi import setup

from sqlalchemy.orm.exc import NoResultFound
from database import db_session as sess
from datamodel import Mentor, Pref, PrefWeight, Choice

@app.route('/mentors')
def list_mentors():
	require_auth('admin')

	pref_types = sess.query(PrefTypes).all()
	prefs = sess.query(Pref).all()

	mentors = sess.query(Mentor).all()
	return render_response('list_mentors.html',locals()) #TODO get rid of locals call?

class MentorsUploadForm(Form):
	name_index = Integer.using(label="Column Index of Mentor's Name")
	new_returning_index = Integer.using(label="Column Index of Whether Mentor is New or Returning")
	pref_start_index = Integer.using(label='Index where preferences start')
	pref_stop_index = Integer.using(label='Index where preferences end')

@app.route('/mentors/upload', methods=['GET','POST'])
def upload_mentors():
	require_auth('admin')

	if request.method == 'POST':
		form_values = request.form.copy
		del form_values['_csrf_token']
		form = MentorsUploadForm.from_flat(form_values)

		locals().update(**form.value) #I'm feel, dirty, but not bad
		reader = csv.reader(request.files['mentors_file'])

		#skip first row which is worthless
		i = iter(reader)
		i.next();

		#save header row
		header_row = i.next()

		for row in i:
			mentor = Mentor()

			mentor.full_name = row[name_index]
			mentor.returning = bool(row[new_returning_index])

			for pref_index in range(pref_start_index, pref_stop_index):
				pref_name = header_row[pref_index].rsplit('...:')[2]
				weight_num = int(row[pref_index])

				choice = Choice()
				choice.pref = sess.query(Pref).filter_by(name=pref_name).one()

				choice.weight = sess.query(PrefWeight).filter_by(
					pref_type_id=chioce.pref.pref_type_id,
					weight_num=weight_num
				)

				mentor.choices.append(choice)

			sess.add(mentor)
		sess.commit()

	else:
		form = MentorsUploadForm()
		pass

	return render_response('upload_mentors.html',dict(form=form))
