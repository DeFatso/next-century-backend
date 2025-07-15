-- USERS
CREATE TABLE
    users (
        id SERIAL PRIMARY KEY,
        full_name VARCHAR(100) NOT NULL,
        email VARCHAR(100) UNIQUE NOT NULL,
        password_hash VARCHAR(255) NOT NULL,
        role VARCHAR(10) CHECK (role IN ('student', 'admin')) NOT NULL,
        profile_pic_url VARCHAR(255), -- optional
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

-- GRADES
CREATE TABLE
    grades (
        id SERIAL PRIMARY KEY,
        name VARCHAR(20) NOT NULL -- e.g., Grade 1
    );

-- SUBJECTS
CREATE TABLE
    subjects (
        id SERIAL PRIMARY KEY,
        name VARCHAR(50) NOT NULL, -- e.g., Mathematics
        grade_id INT REFERENCES grades (id) ON DELETE CASCADE
    );

-- ENROLLMENTS
CREATE TABLE
    enrollments (
        id SERIAL PRIMARY KEY,
        student_id INT REFERENCES users (id) ON DELETE CASCADE,
        grade_id INT REFERENCES grades (id) ON DELETE CASCADE,
        enrolled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

-- LESSONS
CREATE TABLE
    lessons (
        id SERIAL PRIMARY KEY,
        subject_id INT REFERENCES subjects (id) ON DELETE CASCADE,
        title VARCHAR(100) NOT NULL,
        content_text TEXT,
        video_url VARCHAR(255),
        created_by INT REFERENCES users (id) ON DELETE SET NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

-- ASSIGNMENTS
CREATE TABLE
    assignments (
        id SERIAL PRIMARY KEY,
        subject_id INT REFERENCES subjects (id) ON DELETE CASCADE,
        title VARCHAR(100) NOT NULL,
        description TEXT,
        due_date DATE,
        created_by INT REFERENCES users (id) ON DELETE SET NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

-- SUBMISSIONS
CREATE TABLE
    submissions (
        id SERIAL PRIMARY KEY,
        assignment_id INT REFERENCES assignments (id) ON DELETE CASCADE,
        student_id INT REFERENCES users (id) ON DELETE CASCADE,
        file_url VARCHAR(255) NOT NULL,
        submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        grade NUMERIC(5, 2),
        feedback TEXT
    );