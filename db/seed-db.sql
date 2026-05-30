-- Create Table Queries
SET TIME ZONE 'UTC';

-- Categories table
-- Stores predefined problem categories
CREATE TABLE categories (
    category_id INT PRIMARY KEY,
    category_name VARCHAR(100) NOT NULL UNIQUE
);

-- Statuses table
-- Stores predefined report statuses
CREATE TABLE statuses (
    status_id INT PRIMARY KEY,
    status_name VARCHAR(100) NOT NULL UNIQUE
);

-- City reports table
-- Stores all citizen problem reports
CREATE TABLE city_reports (
    ticket_id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    category_id INT NOT NULL,
    status_id INT NOT NULL,
    latitude NUMERIC(8,6) NOT NULL CHECK (latitude BETWEEN -90 AND 90),
    longitude NUMERIC(9,6) NOT NULL CHECK (longitude BETWEEN -180 AND 180),
    image_path TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ,
    resolved_at TIMESTAMPTZ,
    admin_comments TEXT,

    CONSTRAINT fk_city_reports_category
        FOREIGN KEY (category_id)
        REFERENCES categories(category_id),

    CONSTRAINT fk_city_reports_status
        FOREIGN KEY (status_id)
        REFERENCES statuses(status_id)
);

-- Seed Data Queries
-- Insert predefined categories
INSERT INTO categories (category_id, category_name) VALUES
(1, 'Generic'),
(2, 'Road Damage'),
(3, 'Street Lighting'),
(4, 'Cleanliness'),
(5, 'Water Supply'),
(6, 'Green Spaces'),
(7, 'Public Infrastructure'),
(8, 'Abandoned Vehicle');

-- Insert predefined statuses
INSERT INTO statuses (status_id, status_name) VALUES
(1, 'Reported'),
(2, 'In Progress'),
(3, 'Resolved'),
(4, 'Rejected');

-- Example test data
INSERT INTO city_reports (
    title,
    description,
    category_id,
    status_id,
    latitude,
    longitude,
    image_path,
    created_at,
    updated_at,
    resolved_at,
    admin_comments
) VALUES
(
    'Large pothole near Syntagma Square',
    'A large pothole has appeared near the pedestrian crossing close to Syntagma Square. It is difficult for cars and motorcycles to avoid it during traffic.',
    1, 1, 37.975564, 23.734832, 'report1.jpg',
    '2026-05-01 09:15:00', NULL, NULL, NULL
),
(
    'Broken street light in Monastiraki',
    'Not working at night.',
    2, 2, 37.976088, 23.725740, NULL,
    '2026-05-02 20:30:00', '2026-05-03 10:00:00', NULL,
    'Maintenance team has been notified.'
),
(
    'Garbage bags left near Omonia Square',
    NULL,
    3, 1, 37.984149, 23.727984, 'report3.jpg',
    '2026-05-03 08:45:00', NULL, NULL, NULL
),
(
    'Water leak near Panepistimio station',
    'Water is leaking from the pavement near the metro entrance. The area is slippery and pedestrians are walking into the street to avoid it.',
    4, 2, 37.980207, 23.732394, 'report4.jpg',
    '2026-05-04 11:20:00', '2026-05-04 13:00:00', NULL,
    'Water service department is checking the issue.'
),
(
    'Damaged bench in National Garden',
    NULL,
    6, 1, 37.973963, 23.737601, NULL,
    '2026-05-05 12:10:00', NULL, NULL, NULL
),
(
    'Fallen tree branch in Zappeion area',
    'Large branch on the path.',
    5, 3, 37.971532, 23.737870, NULL,
    '2026-05-06 16:40:00', '2026-05-07 09:30:00', '2026-05-07 12:15:00',
    'The branch was removed by the maintenance crew.'
),
(
    'Abandoned vehicle in Kolonaki',
    'An abandoned car has been parked in the same location for several weeks. It has no license plates and takes up a parking space on a narrow street.',
    7, 1, 37.978640, 23.743512, 'report7.jpg',
    '2026-05-07 10:25:00', NULL, NULL, NULL
),
(
    'Damaged sidewalk near Acropolis Museum',
    'Several paving stones are loose and dangerous for pedestrians, especially older people and tourists walking toward the museum entrance.',
    1, 2, 37.968449, 23.728628, NULL,
    '2026-05-08 14:05:00', '2026-05-09 09:00:00', NULL,
    'Repair request has been forwarded.'
),
(
    'Overflowing trash bin in Plaka',
    'Full bin.',
    3, 1, 37.972589, 23.729245, NULL,
    '2026-05-09 18:20:00', NULL, NULL, NULL
),
(
    'Broken traffic sign near Evangelismos',
    NULL,
    6, 2, 37.976246, 23.747196, 'report10.jpg',
    '2026-05-10 07:50:00', '2026-05-10 12:30:00', NULL,
    'Inspection scheduled.'
),
(
    'Street light flickering in Koukaki',
    'A street light keeps flickering during the night and sometimes turns off completely for several minutes.',
    2, 1, 37.962837, 23.721717, NULL,
    '2026-05-11 21:15:00', NULL, NULL, NULL
),
(
    'Bulky waste left on sidewalk in Exarchia',
    'Old furniture and bags left on the sidewalk.',
    3, 1, 37.986173, 23.733130, NULL,
    '2026-05-12 13:35:00', NULL, NULL, NULL
),
(
    'Damaged playground equipment in Pangrati',
    'A swing in the playground is broken and may be dangerous for children. The metal chain appears loose on one side.',
    5, 2, 37.969780, 23.749077, 'report13.jpg',
    '2026-05-13 17:10:00', '2026-05-14 08:20:00', NULL,
    'Technician visit has been scheduled.'
),
(
    'Water drainage problem near Petralona',
    NULL,
    4, 1, 37.968102, 23.709954, NULL,
    '2026-05-14 09:40:00', NULL, NULL, NULL
),
(
    'Large pothole in Neos Kosmos',
    'Pothole on the road.',
    1, 3, 37.957613, 23.728088, NULL,
    '2026-05-15 08:10:00', '2026-05-16 11:00:00', '2026-05-17 15:30:00',
    'Road repair completed.'
),
(
    'Broken public bin near Thiseio',
    NULL,
    3, 1, 37.976690, 23.719266, 'report16.jpg',
    '2026-05-16 15:45:00', NULL, NULL, NULL
),
(
    'Damaged bus stop shelter in Ambelokipi',
    'The glass panel of a bus stop shelter is cracked. There are small glass pieces on the ground and people are waiting close to the road.',
    6, 2, 37.988084, 23.763573, 'report17.jpg',
    '2026-05-17 12:25:00', '2026-05-18 09:10:00', NULL,
    'Replacement panel requested.'
),
(
    'Abandoned motorcycle near Victoria Square',
    'Blocking sidewalk.',
    7, 1, 37.993208, 23.730348, 'report18.jpg',
    '2026-05-18 10:55:00', NULL, NULL, NULL
),
(
    'Broken park light in Pedion tou Areos',
    NULL,
    2, 2, 37.994590, 23.737698, NULL,
    '2026-05-19 19:30:00', '2026-05-20 08:45:00', NULL,
    'Electrician assigned.'
),
(
    'Damaged pavement near Larissa Station',
    'The pavement outside the station has several cracks and uneven areas. People with luggage have difficulty passing through.',
    1, 1, 37.992083, 23.721483, 'report20.jpg',
    '2026-05-20 08:00:00', NULL, NULL, NULL
),
(
    'Illegal dumping near Kerameikos',
    'Several bags of construction waste have been dumped next to the sidewalk. The material looks like broken tiles and plaster.',
    3, 1, 37.978359, 23.711217, NULL,
    '2026-05-21 10:30:00', NULL, NULL, NULL
),
(
    'Street light not working in Gazi',
    NULL,
    2, 1, 37.978202, 23.713824, 'report22.jpg',
    '2026-05-21 22:05:00', NULL, NULL, NULL
),
(
    'Water leak in Kypseli',
    'Water running on street.',
    4, 2, 38.000409, 23.739733, NULL,
    '2026-05-22 07:35:00', '2026-05-22 11:15:00', NULL,
    'Issue forwarded to water maintenance service.'
),
(
    'Broken stairs near Lycabettus Hill',
    'Some steps on the public stairway are cracked and unstable. This is risky because many people use these stairs to walk up the hill.',
    6, 1, 37.981779, 23.744217, NULL,
    '2026-05-22 16:50:00', NULL, NULL, NULL
),
(
    'Tree needs pruning in Ilisia',
    'Branches are blocking part of the sidewalk and touching nearby balconies. Pedestrians have to lower their heads to pass.',
    5, 2, 37.975875, 23.756910, 'report25.jpg',
    '2026-05-23 09:10:00', '2026-05-23 14:00:00', NULL,
    'Green spaces department has been informed.'
),
(
    'Trash around metro entrance in Sepolia',
    'Dirty area.',
    3, 1, 38.002947, 23.713772, NULL,
    '2026-05-23 18:25:00', NULL, NULL, NULL
),
(
    'Abandoned van in Patisia',
    'An old van appears abandoned and has been parked in the same spot for over a month. The tires are flat and it is partially blocking visibility at the corner.',
    7, 2, 38.011349, 23.728371, 'report27.jpg',
    '2026-05-24 11:00:00', '2026-05-25 09:40:00', NULL,
    'Police notification is pending.'
),
(
    'Damaged road surface in Kallithea',
    NULL,
    1, 1, 37.955418, 23.698442, NULL,
    '2026-05-24 13:20:00', NULL, NULL, NULL
),
(
    'Broken water fountain in Piraeus Street area',
    'The public water fountain is broken and water is constantly dripping. The pavement around it is wet.',
    4, 3, 37.978971, 23.704862, NULL,
    '2026-05-25 08:30:00', '2026-05-25 12:10:00', '2026-05-26 10:00:00',
    'The fountain valve was repaired.'
),
(
    'Missing manhole cover near Metaxourgeio',
    'There is an open manhole near the side of the road. This is very dangerous for pedestrians, cyclists and vehicles, especially at night.',
    6, 2, 37.986301, 23.721928, 'report30.jpg',
    '2026-05-25 21:45:00', '2026-05-26 08:15:00', NULL,
    'Marked as urgent. Temporary cover requested.'
);
