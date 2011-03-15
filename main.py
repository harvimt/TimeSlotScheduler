#!/usr/bin/python
import sys,os,os.path
try:
	import configparser
except ImportError:
	import ConfigParser as configparser

import csv
import sqlite3
import re

class Scheduler:
	def __init__(self,conf_file):
		self.conf_file = conf_file

		##Config File
		self.courses_file =         ''
		self.survey_file =          ''
		self.output_file =          ''

		#self.num_configurations =   conf.getint('scheduler','num_configurations') #TODO
		self.idx_submissionKey =    0
		self.idx_name =             0
		self.idx_email=             0
		self.idx_ODIN_ID =          0
		self.idx_owningDept =       0
		self.idx_newReturning =     0
		self.idx_twoSlots =         0
		self.idx_onlineHybrid =     0
		self.idx_timePrefStart =    0
		self.idx_timePrefStop =     0
		self.idx_themePrefStart =   0
		self.idx_themePrefStop =    0
		self.idx_facultyPrefStart = 0
		self.idx_facultyPrefStop =  0

		#weights
		self.cost_timepref = [0] * 8
		self.cost_timepref_none = 0.0
		self.cost_timepref_nopref = 0.0

		self.cost_themepref = [0] * 8
		self.cost_themepref_none = 0.0

		self.cost_facultypref = [0] * 8
		self.cost_facultypref_none = 0.0
		self.cost_facultypref_nopref = 0.0

		self.cost_new_mentor_online = 0.0
		self.cost_uw_mentor_online = 0.0

		#Database
		self.conn = None

		#peform initialization
		self.load_config()
		print("Config Loaded")
		self.validate_config()
		print("Config Valid")
		self.init_db()
		print("DB initialize")
		self.load_weights()
		print("Weights Loaded")
		self.load_courses()
		print("Courses Loaded")
		self.load_mentors()
		print("Mentors Loaded")
		self.gen_views()
		print("Assignment scores calculated")
		self.find_schedules()
		print("Schedule Found")

	def load_config(self):
		"""Loads configuration data from self.conf_file into local fields"""
		conf = configparser.RawConfigParser()
		conf.read(self.conf_file)

		try:
			self.courses_file =         conf.get('scheduler','courses_file')
			self.survey_file =          conf.get('scheduler','survey_file')
			self.output_file =          conf.get('scheduler','output_file')

			#self.num_configurations =   conf.getint('scheduler','num_configurations') #TODO
			self.idx_submissionKey =    conf.getint('scheduler','idx_submissionKey')
			self.idx_name =             conf.getint('scheduler','idx_name')
			self.idx_email=             conf.getint('scheduler','idx_email')
			self.idx_ODIN_ID =          conf.getint('scheduler','idx_ODIN_ID')
			self.idx_owningDept =       conf.getint('scheduler','idx_owningDept')
			self.idx_newReturning =     conf.getint('scheduler','idx_newReturning')
			self.idx_twoSlots =         conf.getint('scheduler','idx_twoSlots')
			self.idx_onlineHybrid =     conf.getint('scheduler','idx_onlineHybrid')
			self.idx_timePrefStart =    conf.getint('scheduler','idx_timePrefStart')
			self.idx_timePrefStop =     conf.getint('scheduler','idx_timePrefStop')
			self.idx_themePrefStart =   conf.getint('scheduler','idx_themePrefStart')
			self.idx_themePrefStop =    conf.getint('scheduler','idx_themePrefStop')
			self.idx_facultyPrefStart = conf.getint('scheduler','idx_facultyPrefStart')
			self.idx_facultyPrefStop =  conf.getint('scheduler','idx_facultyPrefStop')

			#weights
			for i in range(1,8):
				self.cost_timepref[i] = conf.getfloat('weights','cost_timepref_%i'%i)

			self.cost_timepref_none = conf.getfloat('weights','cost_timepref_none')
			self.cost_timepref_nopref = conf.getfloat('weights','cost_timepref_nopref')

			for i in range(1,8):
				self.cost_themepref[i] = conf.getfloat('weights','cost_themepref_%i'%i)
			self.cost_themepref_none = conf.getfloat('weights','cost_themepref_none')

			for i in range(1,8):
				self.cost_facultypref[i] = conf.getfloat('weights','cost_facultypref_%i'%i)
			self.cost_facultypref_none = conf.getfloat('weights','cost_facultypref_none')
			self.cost_facultypref_nopref = conf.getfloat('weights','cost_facultypref_nopref')

			self.cost_new_mentor_online = conf.getfloat('weights','cost_new_mentor_online')
			self.cost_uw_mentor_online = conf.getfloat('weights','cost_uw_mentor_online')

		except configparser.MissingSectionHeaderError:
			print("Missing section header add [scheduler] to the top of your file")
			sys.exit(0)
		except (configparser.NoSectionError,configparser.NoOptionError) as ex:
			print("Error parsing config file, check your settings and the user's manual")
			print(ex)
			sys.exit(0)

	def validate_config(self):
		"""validates the data loaded by self.load_config; exits if there is a problem"""
		if self.idx_timePrefStart > self.idx_timePrefStop:
			print("idx_timePrefStart bigger than idx_timePrefStop review config file settings")
			sys.exit(0)
		if self.idx_themePrefStart > self.idx_themePrefStop:
			print("idx_themePrefStart bigger than idx_themePrefStop review config file settings")
			sys.exit(0)
		if self.idx_facultyPrefStart > self.idx_facultyPrefStop:
			print("idx_facultyPrefStart bigger than idx_facultyPrefStop review config file settings")
			sys.exit(0)

		#idx fields (when ranges are expanded) must for a set
		#(one field can't be mapped to the same column and ranges can't overlap)
		indexes = [
			self.idx_submissionKey,
			self.idx_name,
			self.idx_email,
			self.idx_ODIN_ID,
			self.idx_owningDept,
			self.idx_newReturning,
			self.idx_twoSlots,
			self.idx_onlineHybrid
		] + \
		list(range(
			self.idx_timePrefStart,
			self.idx_timePrefStop
		)) + \
		list(range(
			self.idx_themePrefStart,
			self.idx_themePrefStop
		)) + \
		list(range(
			self.idx_facultyPrefStart,
			self.idx_facultyPrefStop
		))

		if len(indexes) != len(set(indexes)):
			print('Bad idx_* configuration')
			sys.exit(0)

	def init_db(self):
		"""Initialize the local sqlite db from schema.sql in memory"""
		if True:
			#for Testing
			if os.path.exists('scheduler.db'):
				os.remove('scheduler.db')
			self.conn = sqlite3.connect('scheduler.db') #save to file for debugging
		else:
			#TODO
			self.conn = sqlite3.connect(':memory:')

		self.conn.row_factory = sqlite3.Row #enable fetching columns by name and index

		#load sql schema from file
		c = self.conn.cursor()
		c.executescript( open('schema.sql').read())

	#Database helper functions
	def get_id(self,col_name,object_name,add_s=True,**extra_columns):
		"""Get the id for object with name <object_name> in table <table_name>
		inserting a row if it doesn't exist yet
		(the extra_columns feature was being used for storing faculty emails,
		but this wasn't being used, but I'm keeping the feature just in case;
		even though it makes the code kind of ugly)"""

		#return None/NULL if:
		if object_name.upper() in ('','TBD','???'):
			return None
		if 'department' and object_name.upper() == 'STAFF':
			return None

		object_name = object_name.strip()

		c = self.conn.cursor()
		if add_s:
			table_name = col_name + 's'
		else:
			table_name = col_name

		c.execute("SELECT \"%s\" FROM \"%s\" WHERE \"%s\" = ?" % (col_name+'_id', table_name, col_name+'_name'), (object_name,))
		row = c.fetchone()
		if row is None:
			num_placeholders = 1 + len(extra_columns)
			ps_placeholders = ','.join(['"%s"'] * num_placeholders) #percent - ess (%s) placeholders
			qm_placeholders = ','.join('?' * num_placeholders) #question-mark (?) placeholders
			sql_ps = 'INSERT INTO "%s" ('+ps_placeholders+') VALUES ('+qm_placeholders+')'
			sql_tup = (table_name, col_name+'_name') + tuple(extra_columns.keys())
			sql = sql_ps % sql_tup
			sql_ins = (object_name,) + tuple(extra_columns.values())
			c.execute(sql,sql_ins)
				
			self.conn.commit()
			return c.lastrowid
		else:
			return row[0]

	def get_time(self,time_name):
		if time_name.upper() in ('','???','TBD'):
			return None
		
		c = self.conn.cursor()
		c.execute("SELECT time_id FROM times WHERE time_name = ?", (time_name,))
		row = c.fetchone()
		if row is not None:
			return row[0]

		if time_name == 'WEB':
			c.execute("INSERT INTO times (time_name,time_type) VALUES (?,'WEB')",
				(time_name,))
		else:
			#print (time_name)
			match = re.match(r'([MTWRF]+) (\d+) *- *(\d+)(/HYBRID)?',time_name)

			if match is None:
				print(time_name)
			#print(match)
			days = match.group(1)
			time_start = int(match.group(2))
			time_stop = int(match.group(3))
			if match.group(4) is None:
				time_type = 'NORMAL'
			else:
				time_type = 'HYBRID'
			#print(time_type)
			sql = '''
			INSERT INTO times
				(time_name,time_type,M,T,W,R,F,time_start,time_stop)
			VALUES (?,?,?,?,?,?,?,?,?)'''
			c.execute(sql,(time_name,time_type,
				days.find('M') != -1,
				days.find('T') != -1,
				days.find('W') != -1,
				days.find('R') != -1,
				days.find('F') != -1,
				time_start, time_stop))

		self.conn.commit()
		return c.lastrowid

	def get_mentor_id_from_odin(self,odin_id):
		c = self.conn.cursor()
		c.execute("SELECT mentor_id FROM mentors WHERE odin_id = ?",(odin_id,))
		row = c.fetchone()
		if row is None: return None
		else: return row[0]

	#load data from text files into db
	def load_weights(self):
		weight_arrs = [self.cost_timepref, self.cost_themepref, self.cost_facultypref]
		table_names = ['time','theme','faculty']
		sql = 'INSERT INTO "%s" (weight,value) VALUES (?,?)'

		c = self.conn.cursor()
		for table_name, weight_arr in zip(table_names, weight_arrs):
			table_name += '_weight_value'
			for weight, value in enumerate(weight_arr):
				c.execute(sql % table_name, (weight, value))
		self.conn.commit()

	def load_courses(self):
		"""Load courses from self.courses_file into db"""
		courses = csv.DictReader(open(self.courses_file,'r'))
		
		for course in courses:
			course_data = {
				'crn': course['CRN'],
				'course_number': course['Course Number'],
				'dept_id': self.get_id('department',course['Department']),
				'theme_id': self.get_id('theme',course['Theme']),
				'time_id': self.get_time(course['Corresponding Time']),
				'faculty_id': self.get_id('faculty',
					course['Faculty First Name'] + ' ' + course['Faculty Last Name'],
					add_s=False),
				'preassn_mentor_id': self.get_mentor_id_from_odin(course['Assigned Mentor']),
				'online_hybrid': (course['Online Hybrid'] == '1')
			}

			c = self.conn.cursor()
			c.execute(
					"INSERT INTO courses ("
					+ ','.join(course_data.keys()) +
					") VALUES ("
					+ ','.join([':'+x for x in course_data.keys()])+
				")",course_data)
		self.conn.commit()

	def load_mentors(self):
		"""Load mentors from self.survey_file into db"""
		mentors = csv.reader(open(self.survey_file,'r'))

		time_idx_2_id = {}
		theme_idx_2_id = {}
		faculty_idx_2_id = {}

		for i,mentor in enumerate(mentors):
			#skipping row 0, it's basically garbage
			if i == 1:
				#deal with header row
				header_row = mentor

				for idx in range(self.idx_timePrefStart,self.idx_timePrefStop+1):
					name = header_row[idx].split("...-")[-1]
					time_idx_2_id[idx] = self.get_time(name)

				for idx in range(self.idx_themePrefStart,self.idx_themePrefStop+1):
					name = header_row[idx].split("...-")[-1]
					theme_idx_2_id[idx] = self.get_id('theme',name)

				for idx in range(self.idx_facultyPrefStart,self.idx_facultyPrefStop+1):
					name = header_row[idx].split("...-")[-1]
					faculty_idx_2_id[idx] = self.get_id('faculty',name,add_s=False)

			elif i > 1:
				#load data from csv into mentor_data
				mentor_data = {
					'submission_key': mentor[self.idx_submissionKey],
					'full_name': mentor[self.idx_name],
					'email': mentor[self.idx_email],
					'odin_id': mentor[self.idx_ODIN_ID]
				}

				if mentor[self.idx_twoSlots] == "1":
					mentor_data['num_slots'] = 2
				else:
					mentor_data['num_slots'] = 1

				if mentor[self.idx_owningDept] == '':
					mentor_data['owning_department_id'] = None
				else:
					mentor_data['owning_department_id'] = int(mentor[self.idx_owningDept])

				mentor_data['online_hybrid'] = (mentor[self.idx_onlineHybrid] == '1')
				mentor_data['new_returning'] =  (mentor[self.idx_newReturning] == '1')

				#insert mentor_data into db
				c=self.conn.cursor()
				c.execute("""INSERT INTO mentors (
							returning,
							online_hybrid,
							odin_id,
							full_name,
							email,
							slots_available,
							owning_dept
						) VALUES (
							:new_returning,
							:online_hybrid,
							:odin_id,
							:full_name,
							:email,
							:num_slots,
							:owning_department_id
						)""", mentor_data)
				mentor_id = c.lastrowid
				self.conn.commit()

				for idx in range(self.idx_timePrefStart,self.idx_timePrefStop+1):
					if mentor[idx] in ('','0'): continue
					weight = 8 - int(mentor[idx])
					time_id = time_idx_2_id[idx]

					c.execute(
						'''INSERT INTO mentor_time_pref (mentor_id,time_id,weight)
						VALUES (?,?,?)''',
						(mentor_id,time_id,weight)
					)

				for idx in range(self.idx_themePrefStart,self.idx_themePrefStop+1):
					if mentor[idx] in ('','0'): continue
					weight = 8 - int(mentor[idx])
					if weight not in range(1,8):
						weight = 0 #TODO nopref
					theme_id = theme_idx_2_id[idx]
					c.execute(
						'''INSERT INTO mentor_theme_pref (mentor_id,theme_id,weight)
						VALUES (?,?,?)''',
						(mentor_id,theme_id,weight)
					)

				for idx in range(self.idx_facultyPrefStart,self.idx_facultyPrefStop+1):
					if mentor[idx] in ('','0'): continue
					weight = 8 - int(mentor[idx])
					faculty_id = faculty_idx_2_id[idx]
					c.execute(
						'''INSERT INTO mentor_faculty_pref (mentor_id,faculty_id,weight)
						VALUES (?,?,?)''',
						(mentor_id,faculty_id,weight)
					)

	def gen_views(self):
		"""Actually 'materialized' views (create table as select)"""
		c = self.conn.cursor()
		c.execute(open('view.sql').read(), 
			{
				'time_cost_nopref': self.cost_timepref_none,
				'theme_cost_nopref': self.cost_themepref_none,
				'faculty_cost_nopref': self.cost_facultypref_none,
				'unwilling_mentor_online': self.cost_uw_mentor_online,
				'cost_new_mentor_online': self.cost_new_mentor_online
			})

	def find_schedules(self):
		courses = self.conn.cursor()
		assignments = self.conn.cursor()
		schedule = self.conn.cursor()

		schedule.execute("CREATE TABLE schedule ( assn_id int)")
		self.conn.commit()

		courses.execute("SELECT course_id FROM courses ORDER BY RANDOM()")
		for course in courses:
			print("Finding assignment for course %i" % (course['course_id'],))
			assignments.execute("SELECT rowid,* FROM assignments WHERE course_id = ? ORDER BY cost", (course['course_id'],))
			for assignment in assignments:
				#is assignment valid?
				schedule.execute("""
					SELECT (COUNT(A.mentor_id) + 1) > min(A.slots_available)
					FROM schedule S JOIN assignments A ON A.rowid = S.assn_id
					WHERE A.mentor_id = ?
					GROUP BY A.mentor_id""", (assignment['mentor_id'],))
				row = schedule.fetchone()
				if row is not None:
					if row[0]: continue #INVALID out of slots for this mentor
					
					#return TRUE if invalid
					schedule.execute("""
						SELECT
							CASE
								WHEN time_id == :time_id THEN true
								WHEN time_type == 'WEB' OR :time_type == 'WEB' THEN false
								WHEN
									(M AND :M) OR
									(T AND :T) OR
									(W AND :W) OR
									(R AND :R) OR
									(F AND :F)
								THEN
									CASE
										WHEN start_time < :start_time THEN :start_time < end_time
										OTHERWISE start_time < :end_time
									END
								OTHERWISE FALSE
							END
						FROM schedule S JOIN assignments A ON A.mentor_id = S.mentor_id
						WHERE A.mentor_id = :mentor_id
						GROUP BY A.mentor_id""", dict(assignment))

					row = schedule.fetchone()
					if row is not None and row[0]:
						continue
				#made it this far without hitting any continues, so it's valid add it to the table"
				print("Using assignment %i for course %i" % (course['course_id'],assignment['rowid']))
				schedule.execute("INSERT INTO schedule (assn_id) VALUES (?)", (assignment['rowid'],))
				self.conn.commit()
				break

sched = Scheduler('SINQ_survey.conf')
