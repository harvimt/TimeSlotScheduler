import sqlalchemy
from sqlalchemy import Column, Integer, String, Boolean, Time
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, backref
Base = declarative_base()

#assert(sqlalchemy.version >= 0.7.0)

class PrefType(Base):
	__tablename__ = 'pref_types'
	pref_type_id = Column(Integer, Sequence('pref_type_id_seq'), primary_key = True)
	pref_type_name = Column(String(32))

class Pref(Base):
	__tablename__ = 'prefs'

	pref_id = Column(Integer, Sequence('pref_id_seq'), primary_key = True)
	pref_type = relationship(PrefType)

	name = Column(String(32))

class Time(Pref):
	__tablename__ = 'times'

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

class Course(Base):
	__tablename__ = 'courses'

	course_id = Column(Integer, Sequence('course_id_seq'), primary_key = True)
	crn = Column(String(32))
	dept_code = Column(String(8))

	time = relationship(Time)
	prefs = relationship(Pref, order_by=Pref.pref_id)
