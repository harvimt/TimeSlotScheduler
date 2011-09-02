SELECT M.mentor_id, C.course_id, SUM(PW.weight_value)
FROM mentors M, courses C
JOIN course2pref  C2P ON C2P.course_id = C.course_id
JOIN prefs        P   ON P.pref_id = C2P.pref_id
LEFT JOIN choices Ch  ON Ch.mentor_id = M.mentor_id AND Ch.pref_id = P.pref_id
LEFT JOIN pref_weights PW  ON Ch.weight_id = PW.pref_weight_id
GROUP BY M.mentor_id, C.course_id
;
