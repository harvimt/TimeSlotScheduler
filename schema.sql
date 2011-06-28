CREATE TABLE courses (
	course_id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,

	crn VARCHAR NOT NULL,
	dept_id int REFERENCES departments,
	course_number NOT NULL,

	time_id int NOT NULL REFERENCES times,
	theme_id int NOT NULL REFERENCES themes,
	faculty_id int REFERENCES faculty,

	preassn_mentor_id int REFERENCES mentors,
	online_hybrid boolean NOT NULL
);

CREATE TABLE faculty (
	faculty_id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
	faculty_name varchar NOT NULL UNIQUE
);

CREATE TABLE faculty_weight_value (
	weight int NOT NULL PRIMARY KEY,
	value float NOT NULL
);

CREATE TABLE mentors (
	mentor_id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
	returning boolean NOT NULL ,
	online_hybrid boolean NOT NULL ,
	odin_id varchar NOT NULL ,
	full_name varchar NOT NULL ,
	slots_available int NOT NULL ,
	owning_dept INT REFERENCES DEPARTMENTS,
	email varchar NOT NULL
);

CREATE TABLE mentor_time_pref (
	mentor_id int NOT NULL REFERENCES mentors,
	time_id int NOT NULL REFERENCES times,
	weight int NOT NULL REFERENCES time_weight_value
);

CREATE TABLE mentor_theme_pref (
	mentor_id INTEGER NOT NULL REFERENCES mentors,
	theme_id int NOT NULL REFERENCES themes,
	weight int NOT NULL REFERENCES theme_weight_value
);

CREATE TABLE mentor_faculty_pref (
	mentor_id INTEGER NOT NULL,
	faculty_id int NOT NULL,
	weight int NOT NULL REFERENCES faculty_weight_value
);

CREATE TABLE themes (
	theme_id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
	theme_name varchar NOT NULL UNIQUE
);

CREATE TABLE theme_weight_value (
	weight INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
	value float NOT NULL
);

CREATE TABLE times (
	time_id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
	time_name varchar NOT NULL UNIQUE,
	time_type varchar NOT NULL, -- WEB,HYBRID, or NORMAL
	-- days of the week
	M bool,
	T bool,
	W bool,
	R bool,
	F bool,
	time_start int,
	time_stop int,

	CHECK ( time_type IN (
			'WEB', -- web/online only
			'HYBRID', -- online and classroom
			'NORMAL' -- classroom only
		)),
	-- If not web-only then days,time_start
	-- & time_stop must be set
	CHECK (
		CASE WHEN time_type != 'WEB' THEN
			M IS NOT NULL AND
			T IS NOT NULL AND
			W IS NOT NULL AND
			R IS NOT NULL AND
			F IS NOT NULL AND
			time_start IS NOT NULL AND
			time_stop IS NOT NULL
		END
	)
);

CREATE TABLE time_weight_value (
	weight INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
	value float NOT NULL 
);

CREATE TABLE departments (
	department_id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
	department_name varchar NOT NULL UNIQUE
);
