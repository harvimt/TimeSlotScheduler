# coding=UTF-8
"""
Run the actual Scheduler
~~~~~~~~~~~~~~~~~~~~~~~

:Copyright: © 2011 Mark Harviston <infinull@gmail.com>

based off `main.py`

Take Mentors/Coures/Weights information and saves a schedule to the schedules of the table

"""

from sqlalchemy.sql import text
from database import db_session as sess

def calc_assn_weights():
	"""
		For each Course/Mentor pair (referred to as an assignment) calculate the weight value
	"""
	
			#
			#
	text("""INSERT INTO assignments (mentor_id, course_id, cost)
			SELECT M.mentor_id, C.course_id, SUM(COALESCE(PW.weight_value,PT.def_weight_val))
			FROM mentors M, courses C
			JOIN course2pref  C2P ON C2P.course_id = C.course_id
			JOIN prefs        P   ON P.pref_id = C2P.pref_id
			JOIN pref_types   PT  ON PT.pref_type_id = P.pref_type_id
			JOIN pref_weights PW  ON PW.pref_type_id = P.pref_type_id
			LEFT JOIN choices Ch  ON Ch.mentor_id = M.mentor_id AND Ch.weight_id = PW.pref_id
			
