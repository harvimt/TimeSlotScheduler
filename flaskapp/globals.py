import random, string

from flaskapp import app
from flask import session, request, url_for, redirect, get_flashed_messages
from sqlalchemy.orm import sessionmaker

from database import db_session as sess
from datamodel import User

import cas

@app.before_request
def csrf_protect():
	if request.method == "POST":
		token = session.pop('_csrf_token', None)
		if not token or token != request.form.get('_csrf_token'):
			abort(403)

def generate_csrf_token(force=True):
	if force or '_csrf_token' not in session:
		session['_csrf_token'] = \
			''.join([random.choice(string.letters + string.digits) for i in xrange(0,32)])
	return session['_csrf_token']

def make_sql_session():
	return sessionmaker(bind=g)

def get_username():
	if 'REMOTE_USER' in request.environ:
		return request.environ['REMOTE_USER']
	else:
		return None

def require_auth(user_type=None):
	"""aborts on failure"""

	username = cas.validate()
	if username is None: abort(401)

	if user_type is not None:
		if user_type not in ['admin','user']:
			abort(500)
		user = sess.query(User).get(username)
		user.user_type == user_type or abort(403)

@app.context_processor
def template_globals():
	if 'username' in session:
		username = session['username']
	else:
		username = None


	return dict(
		username = username,
		messages = get_flashed_messages(with_categories = True)
	)
