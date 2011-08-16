# coding=UTF-8
"""
Administer Course Info
~~~~~~~~~~~~~~~~~~~~~~

:Copyright © 2011 Mark Harviston <infinull@gmail.com>

"""

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
from datamodel import Course

import cas

@app.route('/courses')
def list_course():
	require_auth('admin')
	courses = sess.query(Course).all()
	return render_response('list_courses.html',dict(courses=users))
