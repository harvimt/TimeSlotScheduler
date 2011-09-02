# coding=UTF-8
"""
SQLAlchemy Declarative Data-Model
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:Copyright © 2011 Mark Harviston <infinull@gmail.com>

Helper methods added as needed with very little symmetry, but I used this idiom quite a bit
__init__ callss update(*args,**kwargs)
then update takes in arguments equal to values

"""

import datetime, re

import sqlalchemy
from sqlalchemy import Column, Integer, String, Boolean, Time, Enum, Sequence, ForeignKey, Float, Table
from sqlalchemy.schema import UniqueConstraint
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
	-`full_name`: user's full name, pulled from LDAP, will often be None
	-`email`:     user's email, pulled from LDAP, will often be None
	"""
	__tablename__ = 'users'

	user_name = Column(String(32), primary_key = True) #CAS/Odin id
	user_type = Column(Enum('admin','user'))

	full_name = None
	email = None

	def __init__(self,*args,**kwargs):
		self.update(*args,**kwargs)

	def update(self, user_name=None, user_type=None, full_name=None, email=None):
		""" like self.__dict__.update(), except SQLAlchemy safe """
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
	weight_type = Column(Enum(
		'weight', #each value weighted from X to Y
		'rank'    #top len(X..Y) values ranked X to Y
	))
	def_weight_val = Column(Float)

	def __init__(self,*args,**kwargs):
		self.weight_type = 'weight'
		#self.weights = []

		self.update(*args,**kwargs)

	def update(self,name=None,weight_type=None,def_weight_val=None,weights=None,pref_type_id=None):
		if name is not None: self.name = name
		if weight_type is not None: self.weight_type = weight_type
		if def_weight_val is not None: self.def_weight_val = def_weight_val
		#NOTE no way to handle `weights`, `pref_type_id` in a nice way

	def __repr__(self):
		return "<PrefType id=%s name=%s>" % (self.pref_type_id, self.name)

##--##

class Pref(Base):
	"""A preference such as pref_type=Faculty name=Bart Massey or pref_type=Time, time=MW 12:30-14:30"""
	__tablename__ = 'prefs'

	pref_id = Column(Integer, Sequence('pref_id_seq'), primary_key = True)
	pref_type_id = Column(Integer, ForeignKey('pref_types.pref_type_id'))

	pref_type = relationship(PrefType,backref=backref('prefs',cascade='all, delete, delete-orphan',order_by=pref_id))

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

	pref_type = relationship(PrefType,backref=backref('weights',order_by=weight_num,cascade='all,delete, delete-orphan'))

	__table_args__ = (UniqueConstraint(pref_type_id, weight_num),)

	def __init__(self,*args,**kwargs):
		self.update(*args,**kwargs)

	def update(self, pref_type_id=None, weight_num=None, weight_value=None):
		if pref_type_id is not None: self.pref_type_id = pref_type_id
		if weight_num is not None: self.weight_num = weight_num
		if weight_value is not None: self.weight_value = weight_value

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

	def __repr__(self):
		return '<Mentor mentor_id=%r full_name=%r' % (self.mentor_id, self.full_name)

	def choices_group_by_type(self,pref_types = None):
		"""Group By pref_type_id, and sort by weight_num"""

		sorted_choices = sorted(self.choices, lambda x,y: cmp(x.pref.pref_type_id, y.pref.pref_type_id))
		prev_type_id = None
		groups = {}
		cur_group = None

		if pref_types is not None:
			for pref_type in pref_types:
				groups[pref_type.pref_type_id] = []

		for choice in sorted_choices:
			if prev_type_id != choice.pref.pref_type_id:
				cur_group = []
				prev_type_id = choice.pref.pref_type_id
				groups[prev_type_id] = cur_group
			cur_group.append(choice)

		for group in groups.values():
			group.sort(lambda x,y: cmp(x.weight.weight_num if x.weight is not None else None, y.weight.weight_num if y.weight is not None else None))

		return groups.values()

##--##

class Choice(Base):
	__tablename__ = 'choices'

	choice_id = Column(Integer, Sequence('choice_id_seq'), primary_key=True)

	pref_id   = Column(Integer, ForeignKey('prefs.pref_id'))
	weight_id = Column(Integer, ForeignKey('pref_weights.pref_weight_id'))
	mentor_id = Column(Integer, ForeignKey('mentors.mentor_id'))

	pref = relationship(Pref)
	weight = relationship(PrefWeight)
	mentor = relationship(Mentor, backref=backref('choices', cascade='all, delete, delete-orphan', order_by=pref_id))

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
		self.start_time = None
		self.stop_time =  None

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
			self.name = 'WEB'
		else:
			days=''
			if self.M: days+='M'
			if self.T: days+='T'
			if self.W: days+='W'
			if self.R: days+='R'
			if self.F: days+='F'
			if self.Sa: days+='Sa'
			if self.Su: days+='Su'

			if self.start_time is None or self.stop_time is None:
				self.name = None
				return

			self.name = '{0} {1.hour:d}{1.minute:02d}-{2.hour:d}{2.minute:02d}'.format(days, self.start_time, self.stop_time)

			if self.time_type == 'hybrid':
				self.name += '/HYBRID'
	
	def parse_name(self,name):
		""" turn """
		self.name = name.upper().strip()
		
		if name == 'WEB':
			self.time_type = 'online'
		else:
			match = re.match(r'(([MTWRF]|SA|SU)+)\s*(\d+)\s*-\s*(\d+)\s*(/\s*HYBRID)?',name)
			if not match:
				app.logger.debug('Time parse failure: RE did not match')
				return False

			days = match.group(1)
			days_good = False
			for day in self.bfieldmap.keys():
				if day.upper() in days:
					days_good = True
					self.update(**{day:True})

			if not days_good:
				app.logger.debug('Time Parse Failure: days bad: days = %r', days)
				return False #at least one day must be present

			try:
				start_time = match.group(3)
				start_time_hours, start_time_mins = int(start_time[0:-2]),int(start_time[-2:])

				stop_time = match.group(4)
				stop_time_hours, stop_time_mins = int(stop_time[0:-2]),int(stop_time[-2:])

				self.start_time = datetime.time(start_time_hours, start_time_mins)
				self.stop_time = datetime.time(stop_time_hours, stop_time_mins)
			except Exception as e:
				app.logger.debug('Time Parse Failure: Exception: %r' % e)
				return False

			if match.group(5) is None:
				self.time_type = 'normal'
			else:
				self.time_type = 'hybrid'

		self.update_name()
		if self.name != name:
			raise Exception('Name (%s) does not match name (%s) after parse' % (self.name, name))

		return True

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

	pre_assn_mentor_odin = Column(String) #TODO deprecate, for now acts as placeholder

	pre_assn_mentor_id = Column(Integer, ForeignKey('mentors.mentor_id'))
	pre_assn_mentor = relationship(Mentor)

	def prefs_as_dict(self):
		r={}
		for pref in self.prefs:
			r[pref.pref_type.name] = pref.name
		return r

##--##

class Assignment(Base):
	__tablename__ = 'assignments'

	assn_id = Column(Integer, Sequence('assn_id_seq'), primary_key = True)

	mentor_id = Column(Integer, ForeignKey('mentors.mentor_id'))
	mentor = relationship(Mentor)

	course_id = Column(Integer, ForeignKey('courses.course_id'))
	course = relationship(Course)

	cost = Column(Float)

##--##

sched2assn = Table('sched2assn', Base.metadata,
	Column('sched_id', Integer, ForeignKey('schedules.sched_id')),
	Column('assn_id', Integer, ForeignKey('assignments.assn_id'))
)

class Schedule(Base):
	__tablename__ = 'schedules'

	sched_id = Column(Integer, Sequence('sched_id_seq'), primary_key = True)
	assignments = relationship(Assignment, secondary=sched2assn)
