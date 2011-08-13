import sqlalchemy
from sqlalchemy import Column, Integer, String, Boolean, Time, Enum, Sequence, ForeignKey
from sqlalchemy.orm import relationship, backref
from database import Base

class User(Base):
	__tablename__ = 'users'

	user_name = Column(String(32), primary_key = True) #CAS/Odin id
	user_type = Column(Enum('admin','user'))

	full_name = None
	email = None

	def __init__(self,user_name,user_type):
		self.user_name = user_name
		self.user_type = user_type

	def __repr__(self):
		return "<User user_name=%s user_type=%s>" % (self.user_name, self.user_type)

##--##

class PrefType(Base):
	__tablename__ = 'pref_types'

	pref_type_id = Column(Integer, Sequence('pref_type_id_seq'), primary_key = True)
	pref_type_name = Column(String(32))

##--##

"""
class Pref(Base):
	__tablename__ = 'prefs'

	pref_id = Column(Integer, Sequence('pref_id_seq'), primary_key = True)
	pref_type = relationship(PrefType)

	name = Column(String(32))

	discriminator = Column('type', String(50))
	#__mapper_args__ = {'polymorphic_on': discriminator}

##--##

class TimePref(Pref):
	__tablename__ = 'times'
	#__mapper_args__ = {'polymorphic_identity': 'time'}

	pref_id = Column(Integer, ForeignKey('prefs.pref_id'), primary_key = True)

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
"""

##--##

class Mentor(Base):
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

class Course(Base):
	__tablename__ = 'courses'

	course_id = Column(Integer, Sequence('course_id_seq'), primary_key = True)
	crn = Column(String(32))
	dept_code = Column(String(8))

	#time = relationship(TimePref)
	#prefs = relationship(Pref, order_by=Pref.pref_id)
