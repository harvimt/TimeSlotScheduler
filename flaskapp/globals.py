import random, string

from flaskapp import app
from flask import session, request, url_for, redirect

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
