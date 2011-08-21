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

from sqlalchemy.orm.exc import NoResultFound
from database import db_session as sess
from datamodel import Mentor, Pref, TimePref, PrefType

@app.route('/mentors')
def list_mentors():
	require_auth('admin')

	pref_types = sess.query(PrefTypes).all()
	prefs = sess.query(Pref).all()

	mentors = sess.query(Mentor).all()
	return render_response('list_mentors.html',locals()) #TODO get rid of locals call?
