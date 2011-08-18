# 
"""
Administrate Preference Weights
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:Copyright (c) 2011 Mark Harviston <infinull@gmail.com>

 * Display the list of pref_types and weights
 * NOTE does not enforce PrefType safety
 * TODO make PrefType proof

"""

import csv, datetime

import flask
from flask import session, request, url_for, redirect, abort, flash

from flaskext.genshi import render_response
from flaskapp.globals import *

from flatland import Form, String, Constrained, Enum, List, Float, Integer
from flatland.validation import NoLongerThan
from flatland.out.genshi import setup

from sqlalchemy.orm.exc import NoResultFound
from database import db_session as sess
from datamodel import PrefType, PrefWeight
from pprint import pformat

class PrefWeightForm(Form):
	weight_value = Float
	weight_num = Integer.using(optional=True)
	pref_type_id = Integer.using(optional=True)

class PrefTypeForm(Form):
	pref_type_id = Integer.using(optional=True)
	name = String.using(label="Pref Type Name",   validators=[NoLongerThan(32)])
	weight_type = Enum.using(label="Weight Type", valid_values=['rank','weight'])
	weights = List.using(label="Weights").of(PrefWeightForm)

class PrefTypesForm(List.of(PrefTypeForm)): pass

@app.route('/weights')
def admin_weights():
	require_auth('admin')
	pref_types = sess.query(PrefType).outerjoin(PrefWeight).all()

	form = PrefTypesForm()
	#app.logger.debug('FType: %s' % type(form))

	for pref_type in pref_types:
		i_form = PrefTypeForm.from_object(pref_type)
		for weight in pref_type.weights:
			i_form['weights'].append(PrefWeightForm.from_object(weight))

		form.append(i_form)

	if request.method == 'POST':
		flash('submitted form') #TODO

	#for pref_type in form:
		#app.logger.debug('Name: %s ' % pformat(pref_type['name']))
		#app.logger.debug('Label: %s ' % pformat(pref_type['name'].label))

	#return render_response('debug.html',dict(message='foo'))
	return render_response('admin_weights.html', dict(pref_types=form))
