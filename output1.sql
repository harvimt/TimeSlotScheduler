SELECT
cost AS COST,
--time_cost,
--theme_cost,
--faculty_cost,
--unwilling_cost,
--untrained_cost,
--SIGNATURE
    CASE WHEN C.online_hybrid AND NOT M.returning THEN 'nm' ELSE '' END || -- new mentor
    CASE WHEN C.online_hybrid AND NOT M.online_hybrid THEN 'uw' ELSE '' END || -- unwilling
    't' || COALESCE(MTP.weight,'-') || -- time
    'h' || COALESCE(MThP.weight,'-') || -- theme
    'f' || COALESCE(MFP.weight,'-') -- faculty
AS SIGNATURE,
COALESCE(Th.theme_name,'Untitled') AS "COURSE TITLE",
COALESCE(F.faculty_name,'TBD') AS "FACULTY NAME",
COALESCE(A.time_name, 'TBD') AS "COURSE TIME",
M.full_name AS "MENTOR NAME",
M.email AS "MENTOR EMAIL"
FROM schedule S
JOIN assignments A ON S.assn_id = A.rowid
JOIN courses C ON A.course_id = C.course_id
JOIN mentors M ON A.mentor_id = M.mentor_id
JOIN themes Th ON C.theme_id = Th.theme_id
JOIN faculty F ON C.faculty_id = F.faculty_id
LEFT JOIN mentor_time_pref MTP ON MTP.mentor_id = M.mentor_id AND MTP.time_id = C.time_id
LEFT JOIN mentor_theme_pref MThP ON MThP.mentor_id = M.mentor_id AND MThP.theme_id = C.theme_id
LEFT JOIN mentor_faculty_pref MFP ON MFP.mentor_id = M.mentor_id AND MFP.faculty_id = C.faculty_id
;
