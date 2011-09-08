# coding=UTF-8
"""
Administrate Mentors
~~~~~~~~~~~~~~~~~~~~

:Copyright © 2011 Mark Harviston <infinull@gmail.com>

 * Display the list of mentors
 * Upload a CSV formatted qualtrics style and load the data
 * TODO make PrefType proof

"""

import csv, datetime, re

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

def excol2in(excol):
  """Exceol Column name (AB) to index"""
  return sum ([ 26**i * (ord(c) - ord('A') + 1) for i, c in enumerate(reversed(excol.upper()))]) - 1

@app.route('/mentors')
def list_mentors():
	require_auth('admin')

	pref_types = sess.query(PrefType) #.outerjoin(Pref).order_by(PrefType.pref_type_id).all()

	mentors = sess.query(Mentor).outerjoin(Choice).join(Pref).outerjoin(PrefWeight).filter(Choice.weight_id != None).order_by(Pref.pref_type_id).all()

	unattached_prefs = sess.query(Pref).filter(~Pref.pref_id.in_(sess.query(Choice.pref_id))).all()

	return render_response('list_mentors.html',locals())
	#return render_response('message.html',dict(title='List Mentors (no implemented)', message='<a href="/mentors/upload">Upload Mentors</a>'))

class MentorsUploadForm(Form):
	name_index = Integer.using(label="Column Index of Mentor's Name")
	odin_id_index = Integer.using(label="Odin name of the Mentor, used for pre-assigning mentors")

	new_returning_index = Integer.using(label="Column Index of Whether Mentor is New or Returning")

	two_slots_index = Integer.using(label="Column Index of Whether Mentor can be assigned 2 slots (leave blank if N/A)", optional=True)

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
		sess.query(Choice).delete()
		sess.commit()

		name_index = form['name_index'].value
		new_returning_index = form['new_returning_index'].value
		two_slots_index = form['two_slots_index'].value
		odin_id_index = form['odin_id_index'].value

		pref_start_index = form['pref_start_index'].value
		pref_stop_index = form['pref_stop_index'].value

		reader = csv.reader(request.files['mentors_file'])

		#skip first row which is worthless
		i = iter(reader)
		i.next();

		#save header row
		header_row = i.next()
		#app.logger.debug('header_row len() = %i' % len(header_row))

		#iterate over the rest of the rows
		errors = []
		for row in i:
			mentor = Mentor()

			mentor.full_name = row[name_index]
			mentor.odin_id = row[odin_id_index]
			mentor.returning = 'returning' in row[new_returning_index].lower()

			mentor.min_slots = 1
			mentor.max_slots = 1

			if two_slots_index is not None and row[two_slots_index] == 'Yes':
				mentor.max_slots = 2

			for pref_index in range(pref_start_index, pref_stop_index+1):

				header_col = header_row[pref_index]

				#app.logger.debug('pref_index=%i' % pref_index)
				#app.logger.debug('header_col=%r' % header_col)

				try:
					pref_name = header_col.rsplit('...-')[1]
				except Exception:
					errors.append('Header row in invalid format, it should be <question>...-<pref name>')
					continue

				choice = Choice()
				try:
					choice.pref = sess.query(Pref).filter_by(name=pref_name).one()
				except NoResultFound:
					errors.append('Prefernce with name %r not found' % pref_name)
					continue

				choice.weight = None
				if row[pref_index] != '' and row[pref_index] != '0':
					choice.weight = None

					if choice.pref.pref_type.weight_type == 'weight':
						#invert so larger number is likes more, and smaller number is likes less
						weight_num = 7 - int(row[pref_index])
					else:
						#for rank types 1 is best (#1 choice), and higher is worse
						weight_num = int(row[pref_index])
						#else: do leave 

					if not weight_num >= 0:
						errors.append('Weight must be in range 0-7, pref weight is %s, preference=%s, mentor=%s, treating as "Default Preference"' %\
								( row[pref_index], choice.pref.name, mentor.full_name))
						continue

					pref_type_id = choice.pref.pref_type_id

					try:
						choice.weight = sess.query(PrefWeight).filter_by(
							pref_type_id=pref_type_id,
							weight_num=weight_num
						).one()
					except NoResultFound:
						errors.append('Weight not found, mentor=%r, pref_type=%r, weight_num = %i' % (mentor, choice.pref.pref_type,weight_num))

				mentor.choices.append(choice)

			app.logger.debug('prefs done; adding mentor %s' % mentor.full_name)
			sess.add(mentor)

		if errors:
			if len(errors) < 10:
				flash('Upload, errors: ' + '\n\n'.join(errors), 'error')
			else:
				flash('Upload, more than 10 errors, showing first 10, errors: ' + '\n\n'.join(errors[:10]), 'error')
				app.logger.error('Upload Mentors (>10, so can\'t see all in flashed messages) Errors: %r' % errors)

		else:
			flash('Successfully Uploaded Mentors')
		


		sess.commit()
		return redirect(url_for('list_mentors'))

	else:
		form = MentorsUploadForm()

	return render_response('upload_mentors.html',dict(form=form))
