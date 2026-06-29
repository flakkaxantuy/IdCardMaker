CREATE TABLE IF NOT EXISTS kandidat (
    id SERIAL PRIMARY KEY,
    nama VARCHAR(255) NOT NULL,
    sizebaju VARCHAR(255) NOT NULL,
    jeniskelamin VARCHAR(255),
    nik VARCHAR(255),
    lokasikerja VARCHAR(255),
    bpo VARCHAR(255),
    tipepemesanan VARCHAR(255),
    img VARCHAR(255),
    is_draft BOOLEAN DEFAULT FALSE
);

CREATE TABLE IF NOT EXISTS kandidathistory (
    id SERIAL PRIMARY KEY,
    nama VARCHAR(255) NOT NULL,
    nik VARCHAR(255) NOT NULL,
    sizebaju VARCHAR(255) NOT NULL,
    lokasikerja VARCHAR(255) NOT NULL,
    bpo VARCHAR(255) NOT NULL,
    tipepemesanan VARCHAR(255) NOT NULL,
    img VARCHAR(255),
    jeniskelamin VARCHAR(255),
    tanggalproses DATE,
    upload_img VARCHAR(255)
);

CREATE TABLE IF NOT EXISTS lokasi_spil (
    id SERIAL PRIMARY KEY,
    namalokasi VARCHAR(255) NOT NULL
);

CREATE TABLE IF NOT EXISTS admins (
    id SERIAL PRIMARY KEY,
    password VARCHAR(255) NOT NULL
);

INSERT INTO lokasi_spil (namalokasi)
VALUES 
    ('Cabang Ambon'),
    ('Cabang Balikpapan'),
    ('Cabang Banjarmasin'),
    ('Cabang Batam'),
    ('Cabang Batulicin'),
    ('Cabang Baubau'),
    ('Cabang Berau'),
    ('Cabang Biak')
ON CONFLICT DO NOTHING;

INSERT INTO admins (password)
SELECT 'admin123' WHERE NOT EXISTS (SELECT 1 FROM admins);
