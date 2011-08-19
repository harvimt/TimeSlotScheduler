# coding=UTF-8
"""
Application Globals
~~~~~~~~~~~~~~~~~~~

:Copyright © 2011 Mark Harviston <infinull@gmail.com>

The plan is to have all modules import * this one so helper utilities can go in here

"""
import random, string

from flaskapp import app
from flask import session, request, url_for, redirect, get_flashed_messages, abort
from sqlalchemy.orm import sessionmaker

from database import db_session as sess
from datamodel import User

from flatland.out.markup import Generator

import cas

def require_auth(user_type=None):
	"""aborts on failure"""

	username = cas.validate()
	if username is None: abort(401)

	if user_type is not None:
		if user_type not in ['admin','user']:
			abort(500)
		user = sess.query(User).get(username)
		user.user_type == user_type or abort(403)

def all_fl_errors(form):
	errors = []
	errors.extend(form.errors)
	for el in form.all_children:
		errors.extend(el.errors)
	return errors

def error_filter(tagname, attrs, contents, context, bind):
	"""
		When we encounter a bind element
		having errors, set the rendered
		tag's class property to 'error'.
	"""

	if bind is None:
		app.logger.debug('element with error nt bound')
	elif bind.valid:
		attrs['class'] = 'error'
	return contents

# Bind error_filter to input tags generation
error_filter.tags = ('input',)

#add globals to templates
@app.context_processor
def template_globals():
	if 'username' in session:
		username = session['username']
	else:
		username = None

	r = dict(
		username = username,
		csrf_token = app.jinja_env.globals['csrf_token'],
		all_fl_errors = all_fl_errors
	)

	return r

#turn this on for debugging

from flatland.signals import validator_validated

#@validator_validated.connect
def monitor_validation(sender, element, state, result):
	# print or logging.debug validations as they happen:
	app.logger.debug( "validation: %s(%s) valid == %r" % (
	  sender, element.flattened_name(), result))
