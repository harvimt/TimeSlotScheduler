"""
Administer user info
list users, add new user, edit user info, etc.
"""

import ldap

import flask
from flask import session, request, url_for, redirect, abort, flash

from flaskext.genshi import render_response

#flatland form processing
from flatland import Form, String, Constrained, Enum
from flatland.validation import NoLongerThan
from flatland.out.genshi import setup

from flaskapp import genshi, app
from flaskapp.globals import *

from database import db_session as sess
from datamodel import User

import cas

## Forms & Validators ##
class UserForm(Form):
	"""Flatland Form for datamodel.User"""
	user_name = String.using(label="Username",validators=[NoLongerThan(32)])
	user_type = Enum.using(label="User Type",valid_values=['admin','user'])

def user_name_does_not_exist(el, state):
	return sess.query(User).get(el['user_name'].value) is None

def odin_name_exists(el,state):
	return get_odin(el['user_name'].value) is not None

class NewUserForm(UserForm):
	validators = [user_name_does_not_exist, odin_name_exists]

## Odin/LDAP helpers ##

def get_odin(odin_name):
	""" get odin information from LDAP """
	l = ldap.open('localhost')
	l.simple_bind()

	s = l.search_s("ou=people,dc=pdx,dc=edu",ldap.SCOPE_SUBTREE,'uid=%s' % odin_name, ['gecos','mailLocalAddress'])

	if not s:
		return None

	full_name = s[0][1]['gecos'][0]
	email_address = s[0][1]['mailLocalAddress'][0]

	#app.logger.debug("full_name = %s" % full_name)

	r = dict(full_name=full_name, email=email_address)

	l.unbind()

	return r

## Pages ##

@app.route('/users')
def list_users():
	"""List Users"""
	require_auth('admin')

	users = sess.query(User).all()
	return render_response('list_users.html',dict(users=users))

@app.route('/user/new')
def new_user():
	"""Display new user creation form"""
	require_auth('admin')

	if flask.g is None:
		form = NewUserForm()
	else:
		form = flask.g
		app.logger.debug('Old Form: %r' % form)
		flask.g = None

	return render_response('add_user.html', dict(form=form,submit_url=url_for('new_user_submit')))

@app.route('/user/new/submit',methods=['POST'])
def new_user_submit():
	"""Process new user creation form"""
	require_auth('admin')

	form = NewUserForm()

	#app.logger.debug('New User Submitted with type: %s' % type(request.form))

	values = request.form.copy()
	del values['_csrf_token']
	
	app.logger.debug('New User Submitted with %r' % values)

	form.set(values)

	app.logger.debug('New User Form Has %r' % form.value)

	if form.validate():
		user = User(**form)
		#sess.add(user)
		#sess.commit()
		flash('Successfully added new user')
		return redirect(url_for('display_user',username=form['user_name'].value))
	else:
		#TODO
		flash('Form Validation Failed')
		flash.g = form
		return redirect(url_for('new_user'))

@app.route('/user/<username>')
def display_user(username):
	"""Display the user's info"""
	require_auth('admin')

	user = sess.query(User).get(username)
	if not user:
		abort(404)

	oinfo = get_odin(username)
	if oinfo is None:
		flash('User info not found in LDAP','error')
		user.email = 'unkown'
		user.full_name = 'unknown'
	else:
		user.email = oinfo['email']
		user.full_name = oinfo['full_name']

	return render_response('display_user.html', dict(user=user))

@app.route('/user/<username>/edit')
def edit_user(username):
	"""Edit the user's info"""

	user = sess.query(User).get(username)
	return 'Edit info for ' + username

@app.route('/user/<username>/edit/submit',methods=['POST'])
def edit_user_submit(username):
	"""Process Edit user submit"""
	return 'Process Edit Form ' + username
