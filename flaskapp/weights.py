#coding=UTF-8
"""
Administrate Preference Weights
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:Copyright © 2011 Mark Harviston <infinull@gmail.com>

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
	def_weight_val = Float.using(label="Default Weight Value")

	weights = List.using(label="Weights").of(PrefWeightForm)

class PrefTypesForm(List.of(PrefTypeForm)): pass

@app.route('/weights',methods=['GET','POST'])
def admin_weights():
	require_auth('admin')
	pref_types = sess.query(PrefType).outerjoin(PrefWeight).all()

	form = PrefTypesForm()

	for pref_type in pref_types:
		i_form = PrefTypeForm.from_object(pref_type)
		for weight in pref_type.weights:
			i_form['weights'].append(PrefWeightForm.from_object(weight))

		form.append(i_form)

	#Handle Form Submission
	if request.method == 'POST':
		form_values = request.form.copy()
		del form_values['_csrf_token']
		form.set_flat(form_values)

		form.validate()
		if form.valid:

			pref_type_ids = []
			for pref_type in form:
				if pref_type['pref_type_id'].value is None:
					pref_type_sqla = PrefType(**pref_type.value)

					for i, weight in enumerate(pref_type['weights']):
						weight_sqla = PrefWeight(**weight.value)
						weight_sqla.weight_num = i

						sess.add(weight_sqla)
						pref_type_sqla.weights.append(weight_sql)

					sess.add(pref_type_sqla)
				else:
					pref_type_sqla = sess.query(PrefType).get(pref_type['pref_type_id'].value)
					pref_type_sqla.update(**pref_type.value)

					#delete any trailing weights in db that aren't in the form
					if len(pref_type['weights']) < len(pref_type_sqla.weights):
						sess.query(PrefWeight).\
							filter(PrefWeight.pref_type_id == pref_type_sqla.pref_type_id).\
							filter(PrefWeight.weight_num >= len(pref_type['weights'])).\
							delete()

					#add empty weight to end of array for each new weight added in the form not in SQLA
					if len(pref_type['weights']) > len(pref_type_sqla.weights):
						for i in range(len(pref_type['weights']) - len(pref_type_sqla.weights)):
							new_weight = PrefWeight(weight_num = len(pref_type_sqla.weights) + i)
							sess.add(new_weight)
							pref_type_sqla.weights.append(new_weight)

					#update values in sqlalchemy based on form values now that both arrays are the same size
					for weight, weight_sqla in zip(pref_type['weights'], pref_type_sqla.weights):
						weight_sqla.update(**weight.value)

					pref_type_ids.append(pref_type['pref_type_id'].value)

				app.logger.debug('ptype: %r' % pref_type_sqla)

			#delete PrefTypes
			if pref_type_ids:
				#app.logger.debug('ids: %r' % pref_type_ids)

				#why can't I just do .delete() again oh cryptic error message?
				ptypes_to_del = sess.query(PrefType).\
					filter( ~PrefType.pref_type_id.in_( pref_type_ids ) ).\
					all()
				for ptype_to_del in ptypes_to_del:
					sess.delete(ptype_to_del)

			sess.commit()
			flash('Successfully Edited Preference Types & Weights')
		else:
			#app.logger.debug(repr(all_fl_errors(form)))
			flash('Form Validation Failed','error')

		#app.logger.debug('valid %r', form.valid)

	return render_response('admin_weights.html', dict(pref_types=form))
