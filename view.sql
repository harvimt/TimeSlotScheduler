-- vim: syn=mysql
CREATE table assignments AS
SELECT
	M.mentor_id,
	C.course_id,
	T.*,
	M.slots_available,
	-- costs
	coalesce(TWV.value,:time_cost_nopref) AS time_cost,
	coalesce(ThWV.value,:theme_cost_nopref) AS theme_cost,
	coalesce(FWV.value,:faculty_cost_nopref) AS faculty_cost,
	CASE WHEN C.online_hybrid AND NOT M.online_hybrid THEN :unwilling_mentor_online ELSE 0.0 END AS unwilling_cost,
	CASE WHEN C.online_hybrid AND NOT M.returning THEN :cost_new_mentor_online ELSE 0.0 END AS untrained_cost,
	0.0 AS cost

FROM mentors M
JOIN courses C ON
	(C.preassn_mentor_id IS NULL OR M.mentor_id = C.preassn_mentor_id) AND
	(M.owning_dept IS NULL OR M.owning_dept = C.dept_id)
LEFT JOIN mentor_time_pref MTP ON MTP.mentor_id = M.mentor_id AND C.time_id = MTP.time_id
LEFT JOIN time_weight_value TWV ON MTP.weight = TWV.weight
LEFT JOIN mentor_theme_pref MThP ON MThP.mentor_id = M.mentor_id AND C.theme_id = MThP.theme_id
LEFT JOIN theme_weight_value ThWV ON MThP.weight = ThWV.weight
LEFT JOIN mentor_faculty_pref FTP ON FTP.mentor_id = M.mentor_id AND C.faculty_id = FTP.faculty_id
LEFT JOIN faculty_weight_value FWV ON FTP.weight = FWV.weight
JOIN times T ON T.time_id = C.time_id
-- LIMIT 100
;
