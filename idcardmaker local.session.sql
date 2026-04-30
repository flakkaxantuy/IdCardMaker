CREATE TABLE IF NOT EXISTS kandidat (
    id SERIAL PRIMARY KEY,
    nama VARCHAR(255) NOT NULL,
    sizebaju VARCHAR(255) NOT NULL
);

CREATE TABLE IF NOT EXISTS kandidathistory (
    id SERIAL PRIMARY KEY,
    nama VARCHAR(255) NOT NULL,
    nik int NOT NULL,
    sizebaju VARCHAR(255) NOT NULL,
    lokasikerja VARCHAR(255) NOT NULL,
    bpo VARCHAR(255) NOT NULL,
    tipepemesanan VARCHAR(255) NOT NULL
);

ALTER TABLE kandidathistory
ADD COLUMN img VARCHAR(255);

ALTER TABLE kandidathistory
ADD COLUMN jeniskelamin VARCHAR(255);

ALTER TABLE kandidat
ADD COLUMN jeniskelamin VARCHAR(255);

ALTER TABLE kandidathistory
ADD COLUMN tanggalproses DATE;

ALTER TABLE kandidathistory
ALTER COLUMN nik TYPE VARCHAR(255);

DELETE FROM kandidat

ALTER TABLE kandidathistory
Drop COLUMN tanggalproses;

SELECT * FROM kandidat

CREATE TABLE IF NOT EXISTS lokasi_spil(
    id SERIAL PRIMARY KEY,
    namalokasi VARCHAR(255) NOT NULL
)   

INSERT INTO lokasi_spil (namalokasi)
VALUES ('Cabang Ambon'),('Cabang Balikpapan'),('Cabang Banjarmasin'),('Cabang Batam'),('Cabang Batulicin'),('Cabang Baubau'),('Cabang Berau'),('Cabang Biak');

ALTER TABLE kandidat
DROP COLUMN lokasikerja;