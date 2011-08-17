# coding=UTF-8
"""
SQLAlchemy Declarative Data-Model
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:Copyright © 2011 Mark Harviston <infinull@gmail.com>

"""

import datetime

import sqlalchemy
from sqlalchemy import Column, Integer, String, Boolean, Time, Enum, Sequence, ForeignKey, Float, Table
from sqlalchemy.orm import relationship, backref
from database import Base

##--##

class User(Base):
	"""
	Represents the sites users, used for authentication
	Some extra information stored in LDAP

	::Members::
	-`user_name`: the user_name
	-`user_type`: the user_type
	-`full_name`: user's full name, pulled from ldap, will often be None
	-`email`:     user's email, pulled from ldap, will often be None
	"""
	__tablename__ = 'users'

	user_name = Column(String(32), primary_key = True) #CAS/Odin id
	user_type = Column(Enum('admin','user'))

	full_name = None
	email = None

	def __init__(self,*args,**kwargs):
		self.update(*args,**kwargs)

	def update(self, user_name=None, user_type=None, full_name=None, email=None):
		""" like self.__dict__.update(), except sqlalchemy safe """
		#TODO: think of a way to do this with reflection/meta-programming

		if user_name is not None: self.user_name = user_name
		if user_type is not None: self.user_type = user_type
		if full_name is not None: self.full_name = full_name
		if email     is not None: self.email = email

	def __repr__(self):
		return "<User user_name=%s user_type=%s>" % (self.user_name, self.user_type)

##--##

class PrefType(Base):
	"""The type of preference, time, faculty, or theme"""
	__tablename__ = 'pref_types'

	pref_type_id = Column(Integer, Sequence('pref_type_id_seq'), primary_key = True)
	name = Column(String(32))

	def __init__(self,*args,**kwargs):
		self.update(*args,**kwargs)

	def update(self,name=None):
		if name is not None: self.name = name

	def __repr__(self):
		return "<PrefType id=%s name=%s>" % (self.pref_type_id, self.pref_type_name)

##--##

class Pref(Base):
	"""A preference such as pref_type=Faculty name=Bart Massey or pref_type=Time, time=MW 12:30-14:30"""
	__tablename__ = 'prefs'

	pref_id = Column(Integer, Sequence('pref_id_seq'), primary_key = True)
	pref_type_id = Column(Integer, ForeignKey('pref_types.pref_type_id'))

	pref_type = relationship(PrefType)

	name = Column(String(32))

	discriminator = Column('type', String(50))
	__mapper_args__ = {'polymorphic_on': discriminator}

	def __str__(self):
		return self.name

##--##

class PrefWeight(Base):
	"""Maps a weight value index (integer) from the survey to the floating-point value used by the algorithm"""
	__tablename__ = 'pref_weights'
	#TODO add UNIQUE CONSTRAINT on (pref_id, weight_num)

	pref_weight_id = Column(Integer, Sequence('pref_weight_id_seq'), primary_key = True)

	weight_num = Column(Integer)
	weight_value = Column(Float)
	
	pref_type_id = Column(Integer, ForeignKey('pref_types.pref_type_id'))

	pref_type = relationship(PrefType)

##--##

class Mentor(Base):
	"""Represents a Mentor"""
	__tablename__ = 'mentors'

	mentor_id = Column(Integer, Sequence('mentor_id_seq'), primary_key = True)
	returning = Column(Boolean)
	online_hybrid = Column(Boolean)
	odin_id = Column(String(32))
	full_name = Column(String(128))
	min_slots = Column(Integer)
	max_slots = Column(Integer)

	email = Column(String(128))

##--##

class Choice(Base):
	__tablename__ = 'choices'

	choice_id = Column(Integer, Sequence('choice_id_seq'), primary_key=True)

	pref_id   = Column(Integer, ForeignKey('prefs.pref_id'))
	weight_id = Column(Integer, ForeignKey('pref_weights.pref_weight_id'))
	mentor_id = Column(Integer, ForeignKey('mentors.mentor_id'))

	pref = relationship(Pref)
	weight = relationship(PrefWeight)
	mentor = relationship(Mentor, backref=backref('choices'))

##--##

class TimePref(Pref):
	__tablename__ = 'times'
	__mapper_args__ = {'polymorphic_identity': 'time'}

	pref_id = Column(Integer, ForeignKey('prefs.pref_id'), primary_key = True)

	time_type = Column(Enum('normal','online','hybrid'))

	#Days of the week
	M = Column(Boolean)
	T = Column(Boolean)
	W = Column(Boolean)
	R = Column(Boolean)
	F = Column(Boolean)
	Sa = Column(Boolean)
	Su = Column(Boolean)

	start_time = Column(Time)
	stop_time = Column(Time)

	def __init__(self,*args,**kwargs):
		self.pref_type_id = 1

		#set defaults
		self.time_type = 'normal'
		self.M = self.T= self.W = self.R = self.F = self.Sa = self.Su = False
		self.start_time = datetime.time.min
		self.stop_time =  datetime.time.min

		self.update(*args,**kwargs)
		self.update_name()
	
	def update(self,
			time_type=None,
			M=None, T=None, W=None, R=None, F=None, Sa=None, Su=None,
			start_time = None, stop_time = None):

		if time_type is not None: self.time_type = time_type
		if M is not None: self.M = M
		if T is not None: self.T = T
		if W is not None: self.W = W
		if R is not None: self.R = R
		if F is not None: self.F = F
		if Sa is not None: self.Sa = Sa
		if Su is not None: self.Su = Su
		if start_time is not None: self.start_time = start_time
		if stop_time  is not None: self.stop_time  = stop_time

		self.update_name()
	
	def update_name(self):
		""" still need to call session.save(self) in order to update db"""
		if self.time_type == 'online':
			self.name = 'ONLINE'
		else:
			days=''
			if self.M: days+='M'
			if self.T: days+='T'
			if self.W: days+='W'
			if self.R: days+='R'
			if self.F: days+='F'
			if self.Sa: days+='Sa'
			if self.Su: days+='Su'

			self.name = '%s %s-%s' % (days, self.start_time.strftime('%H:%M'), self.stop_time.strftime('%H:%M'))

			if self.time_type == 'hybrid':
				self.name += ' HYBRID'
	
	bfieldmap = dict(
		M= 0b0000001,
		T= 0b0000010,
		W= 0b0000100,
		R= 0b0001000,
		F= 0b0010000,
		Sa=0b0100000,
		Su=0b1000000
	)

	def from_bfield(self,bfield):
		d = {}
		for k,v in self.bfieldmap:
			d[k] = (bfield & v) != 0
		self.update(**d)

	def to_bfield():
		bfield = 0b0
		for k,v in self.bfieldmap:
			if self.__dict__[k]: bfield |= v
	
	def overlaps(self,other):
		if (self.to_bfield() & other.to_bfield) != 0:
			if self.start_time == other.start_time and self.stop_time == other.stop_time:
				return True
			elif other.start_time > self.start_time:
				if self.stop_time > other.course.start_time:
					return True
			else: #self.start_time < other.start_time
				if other.stop_time > self.stop_time:
					return True

		return False
	
	def __str__(self):
		return self.name

##--##

course2pref = Table('course2pref', Base.metadata,
	Column('course_id',Integer,ForeignKey('courses.course_id')),
	Column('pref_id',Integer,ForeignKey('prefs.pref_id'))
)

class Course(Base):
	__tablename__ = 'courses'

	course_id = Column(Integer, Sequence('course_id_seq'), primary_key = True)
	crn = Column(String(32))

	time_id = Column(Integer, ForeignKey('times.pref_id'))
	time = relationship(TimePref)

	prefs = relationship(Pref,
			secondary=course2pref,
			order_by=Pref.pref_id)

	def prefs_as_dict(self):
		r={}
		for pref in self.prefs:
			r[pref.pref_type.name] = pref.name
		return r
