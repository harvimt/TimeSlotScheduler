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

from flatland import Form, String, Constrained, Enum, Integer
from flatland.validation import NoLongerThan
from flatland.out.genshi import setup

from sqlalchemy.orm.exc import NoResultFound
from database import db_session as sess
from datamodel import Mentor, Pref, PrefWeight, Choice, PrefType

@app.route('/mentors')
def list_mentors():
	require_auth('admin')

	pref_types = sess.query(PrefType).outerjoin(Pref).order_by(PrefType.pref_type_id).all()
	#map(pref_types,lambda x: sort(x.,lambda y,z:

	mentors = sess.query(Mentor).outerjoin(Choice).join(Pref).outerjoin(PrefWeight).order_by(Pref.pref_type_id).all()

	return render_response('list_mentors.html',locals())
	#return render_response('message.html',dict(title='List Mentors (no implemented)', message='<a href="/mentors/upload">Upload Mentors</a>'))

class MentorsUploadForm(Form):
	name_index = Integer.using(label="Column Index of Mentor's Name")
	odin_id_index = Integer.using(label="Odin name of the Mentor, used for pre-assigning mentors")

	new_returning_index = Integer.using(label="Column Index of Whether Mentor is New or Returning")
	
	pref_start_index = Integer.using(label='Index where preferences start')
	pref_stop_index = Integer.using(label='Index where preferences end')

@app.route('/mentors/upload', methods=['GET','POST'])
def upload_mentors():
	require_auth('admin')

	if request.method == 'POST':
		form_values = request.form.copy()
		del form_values['_csrf_token']
		form = MentorsUploadForm.from_flat(form_values)
		sess.query(Mentor).delete()
		sess.commit()

		name_index = form['name_index'].value
		new_returning_index = form['new_returning_index'].value
		pref_start_index = form['pref_start_index'].value
		pref_stop_index = form['pref_stop_index'].value

		reader = csv.reader(request.files['mentors_file'])

		#skip first row which is worthless
		i = iter(reader)
		i.next();

		#save header row
		header_row = i.next()
		#app.logger.debug('header_row len() = %i' % len(header_row))

		for row in i:
			mentor = Mentor()

			mentor.full_name = row[name_index]
			mentor.returning = bool(row[new_returning_index])

			for pref_index in range(pref_start_index, pref_stop_index):
				app.logger.debug('pref_index=%i' % pref_index)

				header_col = header_row[pref_index]
				#app.logger.debug('header_col=%s' % header_col)

				pref_name = header_col.rsplit('...-')[1]

				choice = Choice()
				try:
					choice.pref = sess.query(Pref).filter_by(name=pref_name).one()
				except NoResultFound:
					flash('Prefernce with name %r not found' % pref_name,'error')
					continue

				if row[pref_index] == '' or row[pref_index] == '0':
					choice.weight = None
				else:
					weight_num = int(row[pref_index]) - 1
					assert(weight_num >= 0)
					pref_type_id = choice.pref.pref_type_id

					try:
						choice.weight = sess.query(PrefWeight).filter_by(
							pref_type_id=pref_type_id,
							weight_num=weight_num
						).one()
					except NoResultFound:
						choice.weight = None

				mentor.choices.append(choice)

			sess.add(mentor)
		sess.commit()
		flash('Successfully Uploaded Mentors')
		return redirect(url_for('list_mentors'))

	else:
		form = MentorsUploadForm()
		pass

	return render_response('upload_mentors.html',dict(form=form))
