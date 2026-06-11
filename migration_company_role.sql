USE pm_internship;

ALTER TABLE users MODIFY COLUMN role ENUM('student', 'admin', 'company') DEFAULT 'student';

ALTER TABLE companies ADD COLUMN user_id INT NULL;
ALTER TABLE companies ADD COLUMN status ENUM('pending', 'approved', 'rejected') DEFAULT 'pending';

UPDATE companies SET status = 'approved' WHERE verified = TRUE;
UPDATE companies SET status = 'pending' WHERE verified = FALSE;