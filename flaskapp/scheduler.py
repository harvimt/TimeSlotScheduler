# coding=UTF-8

"""
Run the actual Scheduler
~~~~~~~~~~~~~~~~~~~~~~~

:Copyright: © 2011 Mark Harviston <infinull@gmail.com>

based off `main.py`

Take Mentors/Coures/Weights information and saves a schedule to the schedules of the table

Meant to be run as a command, not part of the web-app
Designed to be implemented into the web_app at a later date

"""

from sqlalchemy import or_
from sqlalchemy.sql import text

from database import db_session as sess
from datamodel import Assignment, Course, Mentor, Schedule, sched2assn
from itertools import combinations, chain
from copy import copy

import random

import traceback

class MentorSlot:
	def __init__(self,mentor,slot_num):
		self.mentor = mentor
		self.slot_num = slot_num

def print_msg(msg):
	"""Change to do something else if turned into web-app, like concat and display or log to logger"""
	print msg

class Scheduler(object):
	def __init__(self):
		sess.query(Schedule).delete()
		sess.execute(text("DELETE FROM sched2assn")) #FIXME
		sess.commit()

		print_msg('Started Scheduling')

		#delcare data
		self.all_assns = {}

		#Get data out of DB
		self.courses = sess.query(Course).all()
		#courses.append(None) # add NO_ASSIGNMENT

		self.mentors = sess.query(Mentor).all()

		self.pre_assns = []
		self.req_assns = []
		self.add_assns = []
		self.schedule = Schedule()
		#mentor2course = {} #TODO for speeding up assn_valid

		self.req_mentor_slots = [] #required mentor slots
		self.add_mentor_slots = [] #additional mentor slots

		self.req_best_cost = 0
		self.add_best_cost = 0

		self.unassned_courses = set(self.courses) #discard items from this set as courses are assigned

	def run_scheduler(self):
		try:
			self.calc_assn_weights()
			self.perform_pre_assn()
			self.calc_mentor_slots()

			self.assn_req_slots_initial()
			self.assn_req_slots_swaps()

			self.assn_add_slots_initial()
			self.assn_add_slots_swaps()

			self.finalize_schedule()
			self.output_schedule()

		except Exception:
			print_msg('Failed to Schedule, because:')
			print_msg(traceback.format_exc())
		else:
			print_msg('Finished Scheduling')


	def calc_assn_weights(self):
		"""
			For each Course/Mentor pair (referred to as an assignment) calculate the weight value
		"""
		print_msg('Calculating Scores')
		sess.query(Assignment).delete()
		sess.commit()

		#For each pref_type, mentor, course triple, get all choices that match
		sess.execute(text("""
			INSERT INTO assignments (mentor_id, course_id, cost)
			SELECT M.mentor_id, C.course_id, SUM(COALESCE(PW.weight_value, PT.def_weight_val))
			FROM mentors M, courses C
			JOIN course2pref  C2P ON C2P.course_id = C.course_id
			JOIN prefs        P   ON P.pref_id = C2P.pref_id
			JOIN pref_types   PT  ON PT.pref_type_id = P.pref_type_id
			LEFT JOIN choices Ch  ON Ch.mentor_id = M.mentor_id AND Ch.pref_id = P.pref_id
			LEFT JOIN pref_weights PW  ON Ch.weight_id = PW.pref_weight_id
			GROUP BY M.mentor_id, C.course_id
			"""))

		sess.commit()

		#I don't know why these null assignments are getting added to the table
		sess.query(Assignment).filter(or_(Assignment.mentor_id == None, Assignment.course_id == None)).delete()

		sess.commit()

		assignments = sess.query(Assignment).all()
		for assignment in assignments:
			self.all_assns[(assignment.course,assignment.mentor)] = assignment

		print_msg('Succesfully Calculated Scores')

	def perform_pre_assn(self):
		"""
		For each course with a pre-assigned mentor (based on odin id)
			Fetch the mentor with the matching odin id, (can't be found or more than one cause errors)
			set the pre_assn_mentor of the course accordingly
			decrease min_slots and max_slots by one for the mentor accordingly (can't go below zero)
			NOTE: min_slots and max_slots aren't altered only adj_min_slots and adj_max_slots, so that running the scheduler
			multiple times doesn't give different results, adj_min_slots and adj_max_slots are non-persistent attributes
			(they won't be saved in the db)
		"""
		print_msg('Starting to perform Pre-Assignment')
		courses_w_preassn = sess.query(Course).filter(Course.pre_assn_mentor_odin != None).all()


		for mentor in self.mentors:
			mentor.adj_min_slots = mentor.min_slots
			mentor.adj_max_slots = mentor.max_slots

		for course in courses_w_preassn:
			mentor = sess.query(Mentor).filter_by(odin_id=course.pre_assn_mentor_odin).one()
			mentor.adj_min_slots = max(0, mentor.adj_min_slots - 1)
			mentor.adj_max_slots = max(0, mentor.adj_max_slots - 1)
			course.pre_assn_mentor = mentor
			assn = sess.query(Assignment).filter_by(mentor=mentor,course=course).one()
			self.pre_assns.append(assn)
			self.unassned_courses.discard(course)

		sess.commit()

		print_msg('Successfully performed Pre-Assignment')
	
	def calc_mentor_slots(self):
		"""
		Add one mentor slot for each mentor for the number of minimum slots to required mentor slots (req_mentor_slots)
		And one for the difference of max slots and min slots to additional mentor slots (add_mentor_slots)
		"""

		print_msg('Starting to calculate mentor slots')
		for mentor in self.mentors:
			for slot_num in range(0,mentor.adj_min_slots):
				mentor_slot = MentorSlot(mentor,slot_num)
				self.req_mentor_slots.append(mentor_slot)

			for slot_num in range(mentor.adj_min_slots,mentor.adj_max_slots):
				mentor_slot = MentorSlot(mentor,slot_num)
				self.add_mentor_slots.append(mentor_slot)

		print_msg('Finished to calculating mentor slots')

	## Utility -- get assignment object from course,mentor tuple None/NO_ASSIGNMENT safe
	def get_assn(self,course,mentor):
		if (course, mentor) in self.all_assns:
			return self.all_assns[course,mentor]
		else:
			assn = Assignment(course,mentor,cost=0)
			self.all_assns[course,mentor] = assn
			return assn

	## Utility -- is assignment valid
	def assn_valid(self, assns, assn2):
		for assn1 in assns:
			if assn1.mentor == assn2.mentor and assn1.course.time.overlaps(assn2.course.time):
				return False
		return True

	def assn_req_slots_initial(self):
		print_msg('Started Assigning mentors to required slots -- initial schedule')
		#note courses >= mentors for this part, courses will get None/No Assignment

		## Create initial schedule
		tmp_unassned_courses = list(self.unassned_courses)
		self.req_best_cost = 0
		for course in tmp_unassned_courses:
			found_assn = False
			for slot in self.req_mentor_slots:

				assn = self.get_assn(course,slot.mentor)

				assert(assn.cost is not None)

				if self.assn_valid(self.req_assns, assn):
					self.req_assns.append(assn)

					self.req_mentor_slots.remove(slot)
					self.unassned_courses.discard(course)

					self.req_best_cost += assn.cost
					found_assn = True
					break

			if not found_assn:
				assn = self.get_assn(course,None)
				self.req_assns.append(assn)

		assert(not self.req_mentor_slots) #all required mentors slots should be assigned
		assert(len(self.req_assns) == len(tmp_unassned_courses))
		assert((len(self.req_assns) + len(self.pre_assns)) == len(self.courses))

		print_msg('Finished Assigning mentors to required slots -- initial schedule')

	def assn_req_slots_swaps(self):
		print_msg('Started Assigning mentors to required slots -- swap assignments')

		if len(self.req_assns) > 1:
			max_swaps=10 #TODO make parameter
			swaps=0

			cur_best_cost = self.req_best_cost
			cur_assns = copy(self.req_assns)

			#print_msg('req_best_cost=%r' % self.req_best_cost)
			while swaps < max_swaps:
				print '%2.2f%% - %d/%d\r' % ( ( float(swaps+1) / float(max_swaps) )*100,swaps+1,max_swaps),

				swap_perfed = False
				#print_msg('len(cur_assns)=%r' % len(cur_assns))
				#print_msg('len(req_assns)=%r' % len(self.req_assns))

				for assn1, assn2 in combinations(cur_assns,2):
					new_assn1 = self.get_assn(assn1.course, assn2.mentor)
					new_assn2 = self.get_assn(assn2.course, assn1.mentor)

					#print_msg('assn1=%r\nassn2=%r' % (assn1, assn2) )
					#print_msg('new_assn1=%r\nnew_assn2=%r' % (assn1, assn2) )

					#new_assns.append(new_assn1)
					#new_assns.append(new_assn2)

					#new_assns = [assn for assn in cur_assns if assn != assn1 and assn != assn2]
					new_assns = copy(cur_assns)
					new_assns.remove(assn1)
					new_assns.remove(assn2)

					new_cost = sum(map(lambda x: x.cost, new_assns)) + new_assn1.cost + new_assn2.cost

					if new_cost >= cur_best_cost:
						continue #new cost is greater, skip seeing if the swap is valid

					if not self.assn_valid(new_assns,new_assn1):
						continue #not valid

					new_assns.append(assn1)

					if not self.assn_valid(new_assns,new_assn2):
						continue #not valid

					new_assns.append(assn2)

					cur_assns = new_assns
					cur_best_cost = new_cost
					swap_perfed = True
					break

				#while not swap_perfed:
				if False:
					#deterministic swap not perfed, perf random swap instead
					assn1, assn2 = random.sample(cur_assns,2)

					new_assns = copy(cur_assns)
					new_assns.remove(assn1)
					new_assns.remove(assn2)

					new_assn1 = self.get_assn(assn1.course, assn2.mentor)
					new_assn2 = self.get_assn(assn2.course, assn1.mentor)

					if not self.assn_valid(new_assns,new_assn1):
						continue #not valid

					new_assns.append(assn1)

					if not self.assn_valid(new_assns,new_assn2):
						continue #not valid

					new_assns.append(assn2)

					new_cost = sum([assn.cost for assn in cur_assns if assn != assn1 and assn != assn2])
					new_cost += new_assn1.cost + new_assn2.cost

					swap_perfed = True
					cur_assns = new_assns
					cur_best_cost = new_cost

				if cur_best_cost < self.req_best_cost:
					#is the curent cost better than the absolute best cost
					#if it is then our current schedule is better than the best one we'd found
					#so make it so, copy not necessary
					assert(len(self.req_assns) == len(cur_assns))
					self.req_assns = cur_assns
					self.req_best_cost = cur_best_cost

				swaps += 1
		print

		#remove placeholder assignments
		self.unassned_courses = set()
		for assn in self.req_assns:
			if assn.mentor is None:
				#print_msg('assn=%r' % assn)
				self.req_assns.remove(assn)
				self.unassned_courses.add(assn.course)

		#calculate unassned_courses

		print_msg('Started Assigning mentors to required slots -- swap assignments')

	def assn_add_slots_initial(self):
		#note mentors >= courses
		print_msg('Started Assigning mentors to additional slots -- initial')

		for slot in self.add_mentor_slots:
			found_course = False
			for course in self.unassned_courses:
				assn = self.get_assn(course,slot.mentor)

				assert(assn.cost is not None)

				if self.assn_valid(self.add_assns, assn):
					self.add_assns.append(assn)
					self.unassned_courses.discard(course)
					self.add_best_cost += assn.cost
					found_course = True
					break

			if not found_course:
				#print_msg('no course found for assn')
				assn = self.get_assn(None,slot.mentor)

		assert(not self.unassned_courses)
		print_msg('Finished Assigning mentors to additional slots -- initial')

	def assn_add_slots_swaps(self):
		#note mentors >= courses
		print_msg('Started Assigning mentors to additional slots -- swaps')

		if len(self.add_assns) > 1:
			pass #TODO

		#remove placeholder assignments
		for assn in self.add_assns:
			if assn.course is None:
				#print_msg('assn=%r' % assn)
				self.add_assns.remove(assn)

		print_msg('Finished Assigning mentors to additional slots -- swaps')

	def finalize_schedule(self):
		print_msg('Started Finalizing Schedule')

		self.schedule.assignments = self.pre_assns + self.req_assns + self.add_assns

		sess.add(self.schedule)
		sess.commit()

		assert(len(list(self.schedule.assignments)) == len(self.courses))

		print_msg('Finished Finalizing Schedule')
	
	def output_schedule(self):
		print_msg('Started to output schedule')

		print_msg('Courses length=%r' % len(self.courses))
		print_msg('Pre Assigned length=%r' % len(self.pre_assns))
		#for assn in self.pre_assns:
			#print_msg(repr(len(assn)))

		print_msg('Required Assignments length=%r'%len(self.req_assns))
		#for assn in self.req_assns:
			#print_msg(repr(assn))

		print_msg('Additional Assignments length=%r' % len(self.add_assns))
		#for assn in self.add_assns:
			#print_msg(repr(len(assn)))

		print_msg('full Schedule length=%r'%len(self.schedule.assignments))
		#for assn in self.schedule.assignments:
			#print_msg(repr(assn))

		print_msg('req_best_cost=%f' % self.req_best_cost)

		print_msg('Finished output of schedule')

def run_scheduler():
	random.seed()
	Scheduler().run_scheduler()
