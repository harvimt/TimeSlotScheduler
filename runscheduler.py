#!./env/bin/python
import sys,os,os.path,string,re,csv,sqlite3,inflect,copy,random
try:
	import ConfigParser as configparser
except ImportError:
	import ConfigParser as configparser

class Scheduler:
	def __init__(self, conf_file):
		self.conf_file = conf_file

		##Config File
		self.courses_file =         ''
		self.survey_file =          ''
		self.output_file =          ''

		self.num_configurations =   0
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
		self.cost_timepref = {}
		self.cost_timepref_none = 0.0
		self.cost_timepref_nopref = 0.0

		self.cost_themepref = {}
		self.cost_themepref_none = 0.0

		self.cost_facultypref = {}
		self.cost_facultypref_none = 0.0
		self.cost_facultypref_nopref = 0.0

		self.cost_new_mentor_online = 0.0
		self.cost_uw_mentor_online = 0.0

		self.max_swaps = 0

		#Database
		self.conn = None

		#peform Load config, find schedule, output schedule
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
		#print('Trying %i configurations' % self.num_configurations)
		#self.monte_carlo(self.num_configurations)
		self.iterative_deepening()
		print("Schedule Found")
		#self.refine_schedule()
		self.output_schedule()
		print("Schedule Output")

	def load_config(self):
		"""Loads configuration data from self.conf_file into local fields"""
		conf = configparser.RawConfigParser()
		conf.read(self.conf_file)

		try:
			self.courses_file =         conf.get('scheduler','courses_file')
			self.survey_file =          conf.get('scheduler','survey_file')
			self.output_file =          conf.get('scheduler','output_file')

			#adjust paths to be relative to conf file
			conf_dir = os.path.dirname(self.conf_file)
			self.courses_file = os.path.join(conf_dir,self.courses_file)
			self.survey_file = os.path.join(conf_dir,self.survey_file)
			self.output_file = os.path.join(conf_dir,self.output_file)

			self.num_configurations =   conf.getint('scheduler','num_configurations')
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

			self.max_swaps =  conf.getint('scheduler','max_swaps')

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

		indexes_sans_neg1 = [ index for index in indexes if index != -1 ]

		if len(indexes_sans_neg1) != len(set(indexes_sans_neg1)):
			print('Bad idx_* configuration')
			sys.exit(0)

	def load_db(self):
		"""Use instead of init_db() for testing"""
		self.conn = sqlite3.connect('scheduler.db') #save to file for debugging

		self.conn.row_factory = sqlite3.Row #enable fetching columns by name and index

	def init_db(self):
		"""Initialize the local sqlite db from schema.sql in memory"""
		if False:
			#for Testing
			if os.path.exists('scheduler.db'):
				os.remove('scheduler.db')
			self.conn = sqlite3.connect('scheduler.db') #save to file for debugging
		else:
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
			match = re.match(r'([MTWRF]+) (\d+) *- *(\d+)(/HYBRID)?',time_name)

			if match is None:
				if time_name == 'HYBRID':
					raise(Exception('Hybrid courses must still specify a time slot'))
				else:
					raise(Exception('time_name %s not parseable' % time_name))
			days = match.group(1)
			time_start = int(match.group(2))
			time_stop = int(match.group(3))
			if match.group(4) is None:
				time_type = 'NORMAL'
			else:
				time_type = 'HYBRID'
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
			c.executemany(sql % table_name, weight_arr.items())
		self.conn.commit()

	def load_courses(self):
		"""Load courses from self.courses_file into db"""
		courses = csv.DictReader(open(self.courses_file,'r'))

		self.num_courses = 0
		sql = None
		course_datas = []
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

			if sql is None:
				course_keys = ','.join(course_data.keys())
				course_keys_vars = ','.join([':'+x for x in course_data.keys()])
				sql = "INSERT INTO courses (" + course_keys + ") VALUES ( " + course_keys_vars + ")"

			self.num_courses+=1
			course_datas.append(course_data)


		c = self.conn.cursor()
		c.executemany(sql, course_datas)
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
					try:
						name = header_row[idx].split("...-")[-1]
						time_idx_2_id[idx] = self.get_time(name)
					except IndexError:
						if idx not in range(0,len(header_row)):
							raise Exception('Problem with idx_timePrefStart and idx_timePrefStop, a column in the range was not found')
						else:
							print >>sys.stderr, "There was a problem, parsing a time header column for data, This column (\"%s\") will be ignored" % header_row[idx]
				for idx in range(self.idx_themePrefStart,self.idx_themePrefStop+1):
					try:
						name = header_row[idx].split("...-")[-1]
						theme_idx_2_id[idx] = self.get_id('theme',name)
					except IndexError:
						if idx not in range(0,len(header_row)):
							raise Exception('Problem with idx_themePrefStart and idx_themePrefStop, a column in the range was not found or ')
						else:
							print >>sys.stderr, "There was a problem, parsing a theme header column for data, This column (\"%s\") will be ignored" % header_row[idx]

				for idx in range(self.idx_facultyPrefStart,self.idx_facultyPrefStop+1):
					try:
						name = header_row[idx].split("...-")[-1]
						faculty_idx_2_id[idx] = self.get_id('faculty',name,add_s=False)
					except IndexError:
						if idx not in range(0,len(header_row)):
							raise Exception('Problem with idx_facultyPrefStart and idx_facultyPrefStop, a column in the range was not found')
						else:
							print >>sys.stderr, "There was a problem, parsing a faculty header column for data, This column (\"%s\") will be ignored" % header_row[idx]

			elif i > 1:
				#load data from csv into mentor_data
				mentor_data = {
					'submission_key': mentor[self.idx_submissionKey],
					'full_name': mentor[self.idx_name],
					'email': mentor[self.idx_email],
					'odin_id': mentor[self.idx_ODIN_ID]
				}

				if self.idx_twoSlots != -1 and mentor[self.idx_twoSlots] == "1":
					mentor_data['num_slots'] = 2
				else:
					mentor_data['num_slots'] = 1

				if self.idx_owningDept == -1 or mentor[self.idx_owningDept] == '':
					mentor_data['owning_department_id'] = None
				else:
					mentor_data['owning_department_id'] = int(mentor[self.idx_owningDept])

				if self.idx_onlineHybrid == -1:
					mentor_data['online_hybrid'] = False
				else:
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

				datas = []
				sql = 'INSERT INTO mentor_time_pref (mentor_id,time_id,weight) VALUES (?,?,?)'
				for idx in range(self.idx_timePrefStart,self.idx_timePrefStop+1):
					if mentor[idx] in ('','0'): continue
					weight = 8 - int(mentor[idx])
					time_id = time_idx_2_id[idx]

					datas.append((mentor_id,time_id,weight))

				c.executemany(sql,datas)

				sql = 'INSERT INTO mentor_theme_pref (mentor_id,theme_id,weight) VALUES (?,?,?)'
				datas = []
				for idx in range(self.idx_themePrefStart,self.idx_themePrefStop+1):
					if mentor[idx] in ('','0'): continue
					weight = 8 - int(mentor[idx])
					if weight not in range(1,8):
						weight = 0 #TODO nopref
					theme_id = theme_idx_2_id[idx]
					datas.append((mentor_id,theme_id,weight))

				c.executemany(sql,datas)

				sql = 'INSERT INTO mentor_faculty_pref (mentor_id,faculty_id,weight) VALUES (?,?,?)'
				datas=[]

				for idx in range(self.idx_facultyPrefStart,self.idx_facultyPrefStop+1):
					if mentor[idx] in ('','0'): continue
					weight = 8 - int(mentor[idx])
					faculty_id = faculty_idx_2_id[idx]
					datas.append((mentor_id,faculty_id,weight))

				c.executemany(sql,datas)

	def gen_views(self):
		"""Actually 'materialized' views (create table as select)"""
		c = self.conn.cursor()
		c.execute(open('view.sql').read(),{
				'time_cost_nopref': self.cost_timepref_none,
				'theme_cost_nopref': self.cost_themepref_none,
				'faculty_cost_nopref': self.cost_facultypref_none,
				'unwilling_mentor_online': self.cost_uw_mentor_online,
				'cost_new_mentor_online': self.cost_new_mentor_online
			})

		c.execute('UPDATE assignments SET cost = time_cost + theme_cost + faculty_cost + unwilling_cost + untrained_cost')
		self.conn.commit()

	def monte_carlo(self,num_iteratations):
		"""run find_schedule multiple times and keep the one with the lowest score"""
		c = self.conn.cursor()
		c.execute("CREATE TABLE IF NOT EXISTS best_schedule (assn_id INT)")
		old_best_score = None

		for i in range(0,num_iteratations):
			sys.stdout.write("%05i/%05i\r"%(i,num_iteratations))
			sys.stdout.flush()
			
			self.find_schedule()
			c.execute("SELECT sum(cost) FROM assignments WHERE rowid IN (SELECT assn_id FROM schedule)")
			score = c.fetchone()[0]
			if old_best_score is None or score < old_best_score:
				c.execute("DELETE FROM best_schedule")
				c.execute("INSERT INTO best_schedule SELECT assn_id FROM schedule")
				old_best_score = score
		c.execute('DROP TABLE IF EXISTS schedule')
		c.execute('ALTER TABLE best_schedule RENAME TO schedule')
		self.conn.commit()

	def find_schedule(self):
		"""Find a valid (semi-randomly generated), but not optimum schedule and save it in the table `schedule`"""
		courses = self.conn.cursor()
		assignments = self.conn.cursor()
		schedule = self.conn.cursor()
		blacklist = self.conn.cursor()

		schedule.execute("CREATE TABLE IF NOT EXISTS schedule ( assn_id int)")
		blacklist.execute("CREATE TABLE IF NOT EXISTS blacklist ( assn_id int)")
		blacklist.execute("DELETE FROM blacklist")
		blacklist.execute("DELETE FROM schedule")

		#get number of courses
		courses.execute("SELECT count(course_id) FROM courses")
		num_courses = courses.fetchone()[0]
		courses_left_unassigned = num_courses

		#add pre-assigned mentors
		schedule.execute("""
		INSERT INTO schedule ( assn_id )
		SELECT A.rowid FROM assignments A
		JOIN courses C ON C.course_id = A.course_id
		WHERE C.preassn_mentor_id IS NOT NULL
		""")
		courses_left_unassigned -= schedule.rowcount
		self.conn.commit()
		backtrack_count = 0

		while courses_left_unassigned > 0:
			#get courses that haven't been assigned yet in random order
			courses.execute("""
				SELECT C.course_id
				FROM courses C
				WHERE C.course_id NOT IN (
					SELECT A.course_id
					FROM assignments A
					JOIN schedule S ON S.assn_id = A.rowid
				)
				ORDER BY RANDOM()
			""")

			for course in courses:
				#find assignments (that aren't in blacklist) for current course, best first
				assignments.execute("""
					SELECT rowid,*
					FROM assignments
					WHERE
						course_id = ? AND
						rowid NOT IN (
							SELECT assn_id FROM blacklist
						)
					ORDER BY cost ASC
				""", (course['course_id'],))

				assignment_found=False
				first_assn=None
				#iterate through until a valid assignment is found
				#(the first valid assignment will be the best valid assignment)
				tries = 0
				for assignment in assignments:
					tries += 1
					if first_assn is None:
						first_assn = assignment

					if not self.is_assn_valid(assignment): continue

					#made it this far without hitting any continues, so it's valid add it to the table"
					#DEBUG print "found assignment (%i,%i) after %i tries at cost %f " % (assignment['course_id'],assignment['mentor_id'],tries,assignment['cost'])
					schedule.execute("INSERT INTO schedule (assn_id) VALUES (?)", (assignment['rowid'],))
					self.conn.commit()
					assignment_found=True
					courses_left_unassigned -= 1
					break

				if not assignment_found:
					#add mentor
					backtrack_count += 1
					print('backtracking %i ' % backtrack_count)

					#we tried the assignment it didn't work, so add it to the blacklist
					blacklist.execute("""
						INSERT INTO blacklist (assn_id) SELECT rowid FROM assignments
						WHERE mentor_id = ? AND rowid IN (SELECT assn_id FROM schedule)""",
						(first_assn['mentor_id'],))
					schedule.execute("DELETE FROM schedule WHERE assn_id IN (SELECT assn_id FROM blacklist)")
					self.conn.commit()
					courses_left_unassigned += schedule.rowcount

	def iterative_deepening(self):
		class Mentor:
			def __init__(self,mentor_id,num_slots):
				self.mentor_id = mentor_id
				self.num_slots = num_slots

		class MentorSlot:
			def __init__(self,mentor_id,slot_num):
				self.mentor_id = mentor_id
				self.slot_num = slot_num

		class Course:
			def __init__(self,course_id,M,T,W,R,F,start_time,stop_time,is_web):
				self.course_id = course_id
				self.M,self.T,self.W,self.R,self.F = M,T,W,R,F
				self.start_time = start_time
				self.stop_time = stop_time
				self.is_web = is_web

		costs = {}
		class Assignment:
			def __init__(self, course, mentor_slot):
				self.course = course
				self.mentor_slot = mentor_slot

			def cost(self):
				if self.course == NO_ASSIGNMENT:
					return 0
				else:
					return costs[(self.course.course_id,self.mentor_slot.mentor_id)]

		#get data out of sql
		c = self.conn.cursor()
		c.execute("SELECT mentor_id, slots_available FROM mentors")

		mentor_slots = []
		mentors = []
		for mentor in c:
			mentors.append(Mentor(mentor['mentor_id'],mentor['slots_available']))
			for slot in range(0,mentor['slots_available']):
				mentor_slots.append(MentorSlot(mentor['mentor_id'],slot))

		NO_ASSIGNMENT = Course(None,False,False,False,False,False,None,None,False)
		courses = [NO_ASSIGNMENT]
		c.execute("SELECT course_id, M,T,W,R,F, time_start, time_stop, time_type == 'WEB' as is_web "+
				  "FROM courses C JOIN times T on C.time_id = T.time_id")
		for course in c:
			courses.append(Course(
				course['course_id'],
				course['M'],course['T'],course['W'],course['R'],course['F'],
				course['time_start'],course['time_stop'],
				course['is_web']
			))

		#populate costs cache
		c.execute("SELECT course_id, mentor_id, cost FROM assignments")
		for assn_cost in c:
			costs[(assn_cost['course_id'],assn_cost['mentor_id'])] = assn_cost['cost']

		def is_assn_valid(assn1,assns):
			"""Check if assn overlaps with any of the times in assns"""
			for assn2 in assns:
				if  (assn1.course.M and assn2.course.M) or \
					(assn1.course.T and assn2.course.T) or \
					(assn1.course.W and assn2.course.W) or \
					(assn1.course.R and assn2.course.R) or \
					(assn1.course.F and assn2.course.F) :

						if assn1.course.start_time == assn2.course.start_time and assn1.course.stop_time == assn2.course.stop_time:
							return False
						elif assn2.course.start_time > assn1.course.start_time:
							if assn1.course.stop_time > assn2.course.start_time:
								return False
						else: #assn1.course.start_time < assn2.start_time
							if assn2.course.stop_time > assn1.course.stop_time:
								return False
			return True

		def is_valid(schedule):
			"""Check for overlapping mentor assignments in schedule"""

			for mentor in mentors:
				assns = [ assn for assn in schedule if assn.mentor_slot.mentor_id == mentor.mentor_id ]
				for assn1 in assns:
					if not is_assn_valid(assn1, [assn for assn in assns if assn != assn1]):
						return False

			return True

		def copy_sched(schedule):
			"""Copy The Schedule in a 2-deep shallow-ish copy"""
			return [ copy.copy(assn) for assn in schedule ]

		def find_initial_schedule_sql():
			schedule = []

			#self.find_schedule() #schedule saved to `schedule` table
			#return

			#get initial schedule out of SQL
			c.execute("SELECT A.course_id, A.mentor_id "+
					"FROM schedule S "+
					"JOIN assignments A ON A.rowid = S.assn_id")

			used_mentor_slots = [ ]

			for assn in c:
				mentor_slot = [ m for m in mentor_slots if m.mentor_id == assn['mentor_id'] ] [0]
				course = [ co for co in courses if co.course_id == assn['course_id'] ] [0]
				assignment = Assignment(course, mentor_slot)

				used_mentor_slots.append(mentor_slot)
				schedule.append(assignment)

			unused_mentor_slots = [ m for m in mentor_slots if m not in used_mentor_slots]

			for unused_mentor_slot in unused_mentor_slots:
				assignment = Assignment(NO_ASSIGNMENT, unused_mentor_slot)
				schedule.append(assignment)

			return schedule

		
		def find_initial_schedule():
			schedule = []
			slots_available = copy.copy(mentor_slots)
			#calculate assignments
			for course in courses:
				assns_for_course = [ Assignment(course,slot) for slot in slots_available ]
				assns_for_course = sorted(assns_for_course, lambda x,y: cmp(x.cost(), y.cost()))

				for assn in assns_for_course:
					if is_assn_valid(assn,schedule):
						schedule.append(assn)
						slots_available.remove(assn.mentor_slot)
						break

			return schedule

		# This is where all the magic happens #
		def refine_schedule(schedule):
			"""Performs iterative deepening to refine a schedule"""

			cur_sched = copy_sched(schedule)
			cur_cost = sum([assn.cost() for assn in schedule])

			best_sched = copy_sched(schedule)
			best_cost = cur_cost
			
			num_swaps = 0
			max_swaps = self.max_swaps

			print("%i/%i\r" % (num_swaps,max_swaps)),
			while num_swaps < max_swaps:
				go_again = False
				new_schedule = copy_sched(cur_sched)

				for assn1, assn2 in set([ frozenset((assn1,assn2)) for assn1 in new_schedule for assn2 in new_schedule if assn2 != assn1]):

					#if swapping assn1 and assn2 is valid and improves the cost
					#then alter the schedule and recurse

					new_cost = best_cost - assn1.cost() - assn2.cost()
					(assn1.course, assn2.course) = (assn2.course, assn1.course)
					new_cost += assn1.cost() + assn2.cost()

					if new_cost < best_cost and is_valid(new_schedule):
						cur_sched = best_sched = new_schedule
						cur_cost = best_cost = new_cost

						num_swaps += 1
						print "%i/%i\r" % (num_swaps,max_swaps),

						go_again = True
						break
					else:
						(assn1.course, assn2.course) = (assn2.course, assn1.course)

				if not go_again:
					#perform a random swaps until a valid swap is found
					found = False
					while not found:
						assn1, assn2 = random.sample(new_schedule,2)

						new_cost = best_cost - assn1.cost() - assn2.cost()
						(assn1.course, assn2.course) = (assn2.course, assn1.course)
						new_cost += assn1.cost() + assn2.cost()

						if is_valid(new_schedule):
							cur_sched = new_schedule
							cur_cost = new_cost

							num_swaps += 1
							print "%i/%i\r" % (num_swaps,max_swaps),

							found = True
							break
						else:
							(assn1.course, assn2.course) = (assn2.course, assn1.course)

			return best_sched

			#we've reached a the end, meaning we traversed all pairs of assignments to swap the course
			#and none of them were valid or better
			#local maxima, call it good for now

		print("Initial Schedule Found")
		schedule = find_initial_schedule()
		schedule = refine_schedule(schedule)

		#dump schedule into sql
		c.execute("DELETE FROM schedule")
		for assn in schedule:
			if assn.course != NO_ASSIGNMENT:
				c.execute(
					"INSERT INTO schedule (assn_id) "+
					"SELECT rowid FROM assignments WHERE mentor_id = :mentor_id AND course_id = :course_id ",
					{
						'course_id':assn.course.course_id,
						'mentor_id':assn.mentor_slot.mentor_id
					})

	def is_assn_valid(self,assignment):
		"""Checks to see if schedule + assn (an object) is still a valid schedule"""
		c = self.conn.cursor()
		c.execute("""
			SELECT (COUNT(A.mentor_id) + 1) > min(A.slots_available)
			FROM schedule S JOIN assignments A ON A.rowid = S.assn_id
			WHERE A.mentor_id = ?
			GROUP BY A.mentor_id""", (assignment['mentor_id'],))

		row = c.fetchone()
		if row is not None:
			if row[0]: return False #INVALID out of slots for this mentor
			#return 1/TRUE if invalid
			c.execute("""
				SELECT
					CASE
						WHEN time_id == :time_id THEN 1
						WHEN time_type == 'WEB' OR :time_type == 'WEB' THEN 0
						WHEN
							(M AND :M) OR
							(T AND :T) OR
							(W AND :W) OR
							(R AND :R) OR
							(F AND :F)
						THEN
							CASE
								WHEN time_start < :time_start THEN :time_start < time_stop
								ELSE time_start < :time_stop
							END
						ELSE 0
					END
				FROM schedule S JOIN assignments A ON A.rowid = S.assn_id
				WHERE A.mentor_id = :mentor_id
				GROUP BY A.mentor_id""", dict(assignment))

			row = c.fetchone()
			if row is not None and row[0]:
				return False
		return True

	def output_schedule(self):
		"""Output the value of the `schedule` table to a csv"""
		c = self.conn.cursor()
		writer = csv.writer(open(self.output_file,'w'))
		p = inflect.engine()

		c.execute(open("output1.sql",'r').read())
		header_written = False
		for row in c:
			if not header_written:
				writer.writerow(row.keys())
				header_written=True
			
			row_list = []
			for k,v in zip(row.keys(),row):
				if k == 'COST':
					v  = '%0.2f' % v
				else:
					v = str(v)
				row_list.append(v)

			writer.writerow(row_list)

		writer.writerow([])

		c.execute("""
			SELECT
				SUM(cost) AS "TOTAL COST",
				AVG(cost) AS "AVERAGE COST"
			FROM schedule S
			JOIN assignments A ON S.assn_id = A.rowid
		""")
		row = c.fetchone()

		writer.writerow(("TOTAL COST",row['TOTAL COST']))
		writer.writerow(("AVERAGE COST",row['AVERAGE COST']))

		writer.writerow(())

		template=string.Template(open('output2.sql').read())

		writer.writerow(('CHOICE','FREQ','PERCENT'))
		tables = {
				'time': {'default': 9},
				'theme': {'default': 4},
				'faculty': {'default': 4},
		}
		for table,settings in tables.items():
			sql = template.substitute(table=table)
			c.execute(sql,settings)
			header_written = False
			for row in c:
				row_list = []
				for k,v in zip(row.keys(),row):
					if k == 'CHOICE':
						if v == 9:
							v = 'unpreferred %s' % table
						else:
							v = '%s %s choice' % (p.ordinal(v),table)
					elif k == 'PERCENT':
						v  = '%0.02f%%' % v
					else:
						v = str(v)
					row_list.append(v)

				writer.writerow(row_list)
			writer.writerow([])

		c.execute('''
			SELECT
				sum(CASE WHEN C.online_hybrid AND NOT M.returning THEN 1 ELSE 0 END) new_mentors,
				sum(CASE WHEN C.online_hybrid AND NOT M.online_hybrid THEN 1 ELSE 0 END) unwilling,
				COUNT(C.course_id) num_courses
			FROM schedule S
			JOIN assignments A ON A.rowid = S.assn_id
			JOIN courses C ON A.course_id = C.course_id
			JOIN mentors M ON M.mentor_id = A.mentor_id
		''')
		row = c.fetchone()
		writer.writerow(('new mentors teaching online/hybrid',row['new_mentors'],'%0.02f%%' % (row['new_mentors']/row['num_courses'])))
		writer.writerow(('unwilling mentors teaching online/hybrid',row['unwilling'],'%0.02f%%' % (row['unwilling']/row['num_courses'])))

if len(sys.argv) == 2:
	sched = Scheduler(sys.argv[1])
else:
	print "Usage: ./runscheduler.py [config file]"
	sys.exit(1)
