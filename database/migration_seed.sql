-- Migrated from the original RideMate SQLite database.
-- Run after schema.sql.
BEGIN;
INSERT INTO users (id,full_name,student_id,email,department,year,role,password,vehicle_number) VALUES (1,'test user ','cse0001','test@gmail.com','CSE','3rd Year','Driver','scrypt:32768:8:1$v5EId6OCTnnpJA5N$5946f22e5ba481b13c49e2da615223401d0c145fda27119add0dd07ff405fff38d79e6534a87c4e77bd9a5ffbd807f7347590ba49f165e8e5403abaab1ab711c','mh32vb0001') ON CONFLICT DO NOTHING;
INSERT INTO users (id,full_name,student_id,email,department,year,role,password,vehicle_number) VALUES (2,'test user02','cse0002','test2@gmail.com','CSE','3rd Year','Passenger','scrypt:32768:8:1$hSuaYodG99AO1c8u$556cfe14b81e615133b0ae738fa36bf92dfe1583f62b461db698dc855afe8fbd84546972fe8238fc67d24f4a02884944a29f979c58e3a214e5271bc523a0166e',NULL) ON CONFLICT DO NOTHING;
INSERT INTO users (id,full_name,student_id,email,department,year,role,password,vehicle_number) VALUES (3,'vedant','cse006','vedx@gmail.com','CSE','3rd Year','Driver','scrypt:32768:8:1$3RnTJt50TpLSr2NX$9a7456a89e06e81d16128334d1a4f72baef2d0eb29f3b8504a60ce597281350d113dfe27e8c04fd250213885104f9bbb148eb26224dce33a2a156c0d07a86713',NULL) ON CONFLICT DO NOTHING;

INSERT INTO rides (id,driver_id,driver_name,from_location,to_location,ride_date,ride_time,total_seats,available_seats,vehicle_number,status,created_at) VALUES (1,1,'test user ','G H Raisoni college','Khapri metro','2026-08-06','18:26',1,1,'MH01AB1234','Available','2026-08-06 12:56:38') ON CONFLICT DO NOTHING;
INSERT INTO rides (id,driver_id,driver_name,from_location,to_location,ride_date,ride_time,total_seats,available_seats,vehicle_number,status,created_at) VALUES (2,1,'test user ','G H Raisoni college','Khapri metro1','2026-08-06','20:22',1,0,'MH01AC1234','Available','2026-08-06 14:53:00') ON CONFLICT DO NOTHING;
INSERT INTO rides (id,driver_id,driver_name,from_location,to_location,ride_date,ride_time,total_seats,available_seats,vehicle_number,status,created_at) VALUES (3,1,'test user ','GH raisoni parking ','wadi midc ','2026-08-08','20:33',1,1,'MH49CS1234','Available','2026-08-08 15:03:21') ON CONFLICT DO NOTHING;
INSERT INTO rides (id,driver_id,driver_name,from_location,to_location,ride_date,ride_time,total_seats,available_seats,vehicle_number,status,created_at) VALUES (4,1,'test user ','G H Raisoni college','automotive metro','2026-08-08','21:43',2,1,'MH01AC4321','Available','2026-08-08 16:14:06') ON CONFLICT DO NOTHING;
INSERT INTO rides (id,driver_id,driver_name,from_location,to_location,ride_date,ride_time,total_seats,available_seats,vehicle_number,status,created_at) VALUES (5,1,'test user ','G H Raisoni college1','wardha','2026-08-11','21:03',1,0,'MH49CS1456','Available','2026-08-11 15:33:22') ON CONFLICT DO NOTHING;
INSERT INTO rides (id,driver_id,driver_name,from_location,to_location,ride_date,ride_time,total_seats,available_seats,vehicle_number,status,created_at) VALUES (6,3,'vedant','G H Raisoni college','leh ladak','2026-08-03','13:04',2,1,'mh32vb0001','Available','2026-08-12 07:35:05') ON CONFLICT DO NOTHING;
INSERT INTO rides (id,driver_id,driver_name,from_location,to_location,ride_date,ride_time,total_seats,available_seats,vehicle_number,status,created_at) VALUES (7,1,'test user ','G H risoni ','wardha','2026-08-12','19:39',1,1,'MH49CS1456','Available','2026-08-12 14:09:15') ON CONFLICT DO NOTHING;
INSERT INTO rides (id,driver_id,driver_name,from_location,to_location,ride_date,ride_time,total_seats,available_seats,vehicle_number,status,created_at) VALUES (8,1,'test user ','G H Raisoni college','kerela','2026-08-27','19:59',1,1,'MH29T0932','Available','2026-08-27 14:29:50') ON CONFLICT DO NOTHING;
INSERT INTO rides (id,driver_id,driver_name,from_location,to_location,ride_date,ride_time,total_seats,available_seats,vehicle_number,status,created_at) VALUES (9,2,'test user02','G H Raisoni college1','wardha','2026-09-12','21:29',1,1,'mh59bs1234','Available','2026-09-07 15:59:17') ON CONFLICT DO NOTHING;
INSERT INTO rides (id,driver_id,driver_name,from_location,to_location,ride_date,ride_time,total_seats,available_seats,vehicle_number,status,created_at) VALUES (10,1,'test user ','vasudev','deep joshi art','2026-09-10','21:14',1,0,'mh 49 da 5000','Available','2026-09-10 15:45:33') ON CONFLICT DO NOTHING;

INSERT INTO bookings (id,ride_id,passenger_id,booking_status,booked_at) VALUES (1,1,2,'Rejected','2026-08-06 13:03:18') ON CONFLICT DO NOTHING;
INSERT INTO bookings (id,ride_id,passenger_id,booking_status,booked_at) VALUES (2,2,2,'Accepted','2026-08-06 14:53:33') ON CONFLICT DO NOTHING;
INSERT INTO bookings (id,ride_id,passenger_id,booking_status,booked_at) VALUES (3,4,2,'Accepted','2026-08-08 16:14:31') ON CONFLICT DO NOTHING;
INSERT INTO bookings (id,ride_id,passenger_id,booking_status,booked_at) VALUES (4,5,2,'Accepted','2026-08-11 15:34:00') ON CONFLICT DO NOTHING;
INSERT INTO bookings (id,ride_id,passenger_id,booking_status,booked_at) VALUES (5,6,2,'Accepted','2026-08-12 07:36:37') ON CONFLICT DO NOTHING;
INSERT INTO bookings (id,ride_id,passenger_id,booking_status,booked_at) VALUES (7,8,2,'Rejected','2026-08-27 14:30:15') ON CONFLICT DO NOTHING;
INSERT INTO bookings (id,ride_id,passenger_id,booking_status,booked_at) VALUES (8,10,2,'Accepted','2026-09-10 15:47:04') ON CONFLICT DO NOTHING;

INSERT INTO notifications (id,email,title,message,status) VALUES (1,'test2@gmail.com','Ride Booking Accepted','Your ride booking has been accepted by the driver.','Read') ON CONFLICT DO NOTHING;
INSERT INTO notifications (id,email,title,message,status) VALUES (2,'test2@gmail.com','Ride Booking Rejected','Your ride booking request was rejected by the driver.','Read') ON CONFLICT DO NOTHING;
INSERT INTO notifications (id,email,title,message,status) VALUES (3,'test2@gmail.com','Ride Booking Accepted','Your ride booking has been accepted by the driver.','Read') ON CONFLICT DO NOTHING;

SELECT setval(pg_get_serial_sequence('users','id'), COALESCE((SELECT MAX(id) FROM users), 1), true);
SELECT setval(pg_get_serial_sequence('rides','id'), COALESCE((SELECT MAX(id) FROM rides), 1), true);
SELECT setval(pg_get_serial_sequence('bookings','id'), COALESCE((SELECT MAX(id) FROM bookings), 1), true);
SELECT setval(pg_get_serial_sequence('notifications','id'), COALESCE((SELECT MAX(id) FROM notifications), 1), true);
COMMIT;