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

#add globals to templates
@app.context_processor
def template_globals():
	if 'username' in session:
		username = session['username']
	else:
		username = None

	r = dict(
		username = username,
		csrf_token = app.jinja_env.globals['csrf_token']
	)

	return r
