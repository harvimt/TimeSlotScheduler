SELECT
cost AS COST,
'todo' AS SIGNATURE,
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
