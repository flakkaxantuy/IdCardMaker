from fastapi import FastAPI, Request, Form, status, File, UploadFile, Cookie, Query
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse, StreamingResponse
from pythontopsql import get_db_connection
from PIL import Image, ImageDraw, ImageFont, ImageOps
import os
import uuid
import smtplib
import random
import string
import io
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from datetime import date
TEMPLATE_PATH = "static/template.png"

PHOTO_BOX = (593, 1072, 1398, 2275)                             

PHOTO_W   = PHOTO_BOX[2] - PHOTO_BOX[0]          

PHOTO_H   = PHOTO_BOX[3] - PHOTO_BOX[1]           

CARD_CENTER_X   = 996                                   

NAME_Y_CENTER   = 2500                                  

NIK_Y_CENTER    = 2715                                 

import platform
if platform.system() == "Windows":

    FONT_BOLD = "C:\\Windows\\Fonts\\arialbd.ttf"

    FONT_REG  = "C:\\Windows\\Fonts\\arial.ttf"

else:

    FONT_BOLD = "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"

    FONT_REG  = "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"

def generate_random_nik():

    return ''.join(random.choices(string.digits, k=10))

def generate_idcard(photo_path: str, name: str, nik: str, output_path: str) -> None:
    card = Image.open(TEMPLATE_PATH).convert("RGBA")

    if os.path.exists(photo_path) and photo_path != "static/default_placeholder.png":
        photo = Image.open(photo_path)
        photo = ImageOps.exif_transpose(photo).convert("RGBA")
    else:
        photo = Image.new("RGBA", (PHOTO_W, PHOTO_H), (200, 200, 200, 255))

    pw, ph = photo.size
    box_aspect = PHOTO_W / PHOTO_H
    photo_aspect = pw / ph
    if photo_aspect > box_aspect:
        new_h = PHOTO_H
        new_w = int(PHOTO_H * photo_aspect)
    else:
        new_w = PHOTO_W
        new_h = int(PHOTO_W / photo_aspect)
    photo_resized = photo.resize((new_w, new_h), Image.LANCZOS)
    crop_left = (new_w - PHOTO_W) // 2
    crop_top = (new_h - PHOTO_H) // 2
    photo_cropped = photo_resized.crop((crop_left, crop_top, crop_left + PHOTO_W, crop_top + PHOTO_H))

    card.paste(photo_cropped, (PHOTO_BOX[0], PHOTO_BOX[1]))

    draw = ImageDraw.Draw(card)

    try:

        font_name = ImageFont.truetype(FONT_BOLD, 135)

        font_rest = ImageFont.truetype(FONT_REG, 135)

        font_nik  = ImageFont.truetype(FONT_BOLD,  100)

    except IOError:

        font_name = ImageFont.load_default()

        font_rest = font_name

        font_nik  = font_name

    name_upper = name.upper()

    parts = name_upper.split(" ", 1)

    first = parts[0]

    rest = parts[1] if len(parts) > 1 else ""

    bbox_first = draw.textbbox((0, 0), first, font=font_name)

    w_first = bbox_first[2] - bbox_first[0]

    bbox_rest = draw.textbbox((0, 0), " "+ rest, font= font_rest)

    w_rest = bbox_rest[2] - bbox_rest[0]

    x_start = CARD_CENTER_X - (w_first + w_rest) // 2

    draw.text((x_start, NAME_Y_CENTER), first, font=font_name, fill="black")

    draw.text((x_start + w_first, NAME_Y_CENTER), " " + rest, font=font_rest, fill="black")

    bbox_n = draw.textbbox((0, 0), nik, font=font_nik)

    tw2 = bbox_n[2] - bbox_n[0]

    th2 = bbox_n[3] - bbox_n[1]

    draw.text((CARD_CENTER_X - tw2 // 2, NIK_Y_CENTER - th2 // 2), nik, font=font_nik, fill="black")

    card.convert("RGB").save(output_path, "JPEG", quality=95)

def generate_idcard_bytes(photo_path: str, name: str, nik: str) -> io.BytesIO:
    card = Image.open(TEMPLATE_PATH).convert("RGBA")

    if os.path.exists(photo_path) and photo_path != "static/default_placeholder.png":
        photo = Image.open(photo_path)
        photo = ImageOps.exif_transpose(photo).convert("RGBA")
    else:
        photo = Image.new("RGBA", (PHOTO_W, PHOTO_H), (200, 200, 200, 255))

    pw, ph = photo.size
    box_aspect = PHOTO_W / PHOTO_H
    photo_aspect = pw / ph
    if photo_aspect > box_aspect:
        new_h = PHOTO_H
        new_w = int(PHOTO_H * photo_aspect)
    else:
        new_w = PHOTO_W
        new_h = int(PHOTO_W / photo_aspect)
    photo_resized = photo.resize((new_w, new_h), Image.LANCZOS)
    crop_left = (new_w - PHOTO_W) // 2
    crop_top = (new_h - PHOTO_H) // 2
    photo_cropped = photo_resized.crop((crop_left, crop_top, crop_left + PHOTO_W, crop_top + PHOTO_H))

    card.paste(photo_cropped, (PHOTO_BOX[0], PHOTO_BOX[1]))

    draw = ImageDraw.Draw(card)

    try:

        font_name = ImageFont.truetype(FONT_BOLD, 135)

        font_rest = ImageFont.truetype(FONT_REG, 135)

        font_nik  = ImageFont.truetype(FONT_BOLD,  100)

    except IOError:

        font_name = ImageFont.load_default()

        font_rest = font_name

        font_nik  = font_name

    name_upper = name.upper()

    parts = name_upper.split(" ", 1)

    first = parts[0]

    rest = parts[1] if len(parts) > 1 else ""

    bbox_first = draw.textbbox((0, 0), first, font=font_name)

    w_first = bbox_first[2] - bbox_first[0]

    bbox_rest = draw.textbbox((0, 0), " "+ rest, font= font_rest)

    w_rest = bbox_rest[2] - bbox_rest[0]

    x_start = CARD_CENTER_X - (w_first + w_rest) // 2

    draw.text((x_start, NAME_Y_CENTER), first, font=font_name, fill="black")

    draw.text((x_start + w_first, NAME_Y_CENTER), " " + rest, font=font_rest, fill="black")

    bbox_n = draw.textbbox((0, 0), nik, font=font_nik)

    tw2 = bbox_n[2] - bbox_n[0]

    th2 = bbox_n[3] - bbox_n[1]

    draw.text((CARD_CENTER_X - tw2 // 2, NIK_Y_CENTER - th2 // 2), nik, font=font_nik, fill="black")

    img_byte_arr = io.BytesIO()

    card.convert("RGB").save(img_byte_arr, "JPEG", quality=95)

    img_byte_arr.seek(0)

    return img_byte_arr

def crop_save_uploaded_photo(file_bytes: bytes, output_path: str) -> None:
    photo = Image.open(io.BytesIO(file_bytes))
    photo = ImageOps.exif_transpose(photo).convert("RGBA")
    pw, ph = photo.size
    box_aspect = PHOTO_W / PHOTO_H
    photo_aspect = pw / ph
    if photo_aspect > box_aspect:
        new_h = PHOTO_H
        new_w = int(PHOTO_H * photo_aspect)
    else:
        new_w = PHOTO_W
        new_h = int(PHOTO_W / photo_aspect)
    photo_resized = photo.resize((new_w, new_h), Image.LANCZOS)
    crop_left = (new_w - PHOTO_W) // 2
    crop_top = (new_h - PHOTO_H) // 2
    photo_cropped = photo_resized.crop((crop_left, crop_top, crop_left + PHOTO_W, crop_top + PHOTO_H))
    photo_cropped.convert("RGB").save(output_path, "JPEG", quality=95)

app = FastAPI()

templates = Jinja2Templates(directory="templates")

app.mount("/app/europa/static", StaticFiles(directory="static"), name="static")

UPLOAD_DIR ="static/uploads"

UPLOAD_DIR_idcard ="static/idcardphoto"

os.makedirs(UPLOAD_DIR, exist_ok=True)

os.makedirs(UPLOAD_DIR_idcard, exist_ok=True)


def send_email(nama, nik, sizebaju, jeniskelamin, lokasi, bpo, tipepemesanan, idcard_path):
    msg = MIMEMultipart()
    msg["Subject"] = f"ID Card Karyawan Baru : {nama} ({sizebaju}) - {lokasi}"
    msg["From"] = "notif.pe@spil.co.id"

    to_emails = ["purchasing1@spil.co.id", "frontline.ga@spil.co.id", "hendardi.agustino@spil.co.id"]
    cc_emails = ["hradministrative@spil.co.id", "thomas.nikijuluw@jkt.spil", "regina.cynthia@spil.co.id"]

    msg["To"] = ", ".join(to_emails)
    msg["Cc"] = ", ".join(cc_emails)
    all_recipients = to_emails + cc_emails         
    body = f"""
        <h2>Dear Pak Hendardi,</h2>
    
        Mohon Approvalnya untuk permintaan berikut ini dengan no. BPO: {bpo}<br>
        
        <h2>Dear Tim YES,</h2>
        
        Berikut kami informasikan karyawan baru yang harus dipesankan ID Card dan Seragamnya mohon segera diproses setelah approval BPO<br>
        dari Pak Haryo, detail karyawan sebagai berikut:<br>
 
        <h3>Detail Karyawan :</h3>
 
        Nama Karyawan : {nama}<br>
        Ukuran Seragam : {sizebaju}<br>
        Lokasi : {lokasi}<br>
        No. BPO : {bpo}<br><br>
 
        Berikut kami lampirkan Foto ID Card yang dapat didownload<br>
        Demikian kami sampaikan,</br> 
        Terima Kasih.
        """
    msg.attach(MIMEText(body, "html"))
    
    with open(idcard_path, "rb") as attachment:
        part = MIMEBase("application", "octet-stream")
        part.set_payload(attachment.read())
        
    encoders.encode_base64(part)
    filename = f"IDCard_{nama}.jpg"
    part.add_header(
        "Content-Disposition",
        f"attachment; filename={filename}"
    )
    msg.attach(part)
    
    smtp_host = os.getenv("SMTP_HOST", "mail.spil.co.id")
    smtp_port = int(os.getenv("SMTP_PORT", "465"))
    smtp_user = os.getenv("SMTP_USER", "notif.pe@spil.co.id")
    smtp_pass = os.getenv("SMTP_PASS", "hWN-5j_jDx")
 
    with smtplib.SMTP_SSL(smtp_host, smtp_port) as server:
        server.login(smtp_user, smtp_pass)
        print("Masuk Email")
        server.send_message(msg)


@app.on_event("startup")
def startup_db():
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        
        # 1. Create admins table if not exists
        cur.execute("""
            CREATE TABLE IF NOT EXISTS admins (
                id SERIAL PRIMARY KEY,
                password VARCHAR(255) NOT NULL
            );
        """)
        
        # 2. Insert default admin password if empty
        cur.execute("SELECT COUNT(*) FROM admins;")
        if cur.fetchone()[0] == 0:
            cur.execute("INSERT INTO admins (password) VALUES ('admin123');")
            
        # 3. Create lokasi_spil table if not exists
        cur.execute("""
            CREATE TABLE IF NOT EXISTS lokasi_spil (
                id SERIAL PRIMARY KEY,
                namalokasi VARCHAR(255) NOT NULL
            );
        """)
        
        # 4. Insert locations if empty
        cur.execute("SELECT COUNT(*) FROM lokasi_spil;")
        if cur.fetchone()[0] == 0:
            cur.execute("""
                INSERT INTO lokasi_spil (namalokasi)
                VALUES 
                    ('Cabang Ambon'),
                    ('Cabang Balikpapan'),
                    ('Cabang Banjarmasin'),
                    ('Cabang Batam'),
                    ('Cabang Batulicin'),
                    ('Cabang Baubau'),
                    ('Cabang Berau'),
                    ('Cabang Biak');
            """)
            
        # 5. Add new columns to kandidat table if not exists
        cur.execute("ALTER TABLE kandidat ADD COLUMN IF NOT EXISTS nik VARCHAR(255);")
        cur.execute("ALTER TABLE kandidat ADD COLUMN IF NOT EXISTS lokasikerja VARCHAR(255);")
        cur.execute("ALTER TABLE kandidat ADD COLUMN IF NOT EXISTS bpo VARCHAR(255);")
        cur.execute("ALTER TABLE kandidat ADD COLUMN IF NOT EXISTS tipepemesanan VARCHAR(255);")
        cur.execute("ALTER TABLE kandidat ADD COLUMN IF NOT EXISTS img VARCHAR(255);")
        cur.execute("ALTER TABLE kandidat ADD COLUMN IF NOT EXISTS is_draft BOOLEAN DEFAULT FALSE;")
        
        # 6. Add new columns to kandidathistory table if not exists
        cur.execute("ALTER TABLE kandidathistory ADD COLUMN IF NOT EXISTS upload_img VARCHAR(255);")
        cur.execute("ALTER TABLE kandidathistory ADD COLUMN IF NOT EXISTS jeniskelamin VARCHAR(255);")
        cur.execute("ALTER TABLE kandidathistory ADD COLUMN IF NOT EXISTS tanggalproses DATE;")
        
        conn.commit()
        print("Database migrations applied successfully!")
    except Exception as e:
        print(f"Error altering table on startup: {e}")
        conn.rollback()
    finally:
        conn.close()

@app.get("/app/europa/form")

def kform(request: Request):

    return templates.TemplateResponse(request, "kform.html")

@app.get("/app/europa/submitted")

def kform_submited(request: Request):

    return templates.TemplateResponse(request, "ksubmited.html")

@app.post("/app/europa/form")

async def submit_kform(

    nama: str = Form(...),

    sizebaju: str = Form(...),

    jeniskelamin: str = Form(...),

    img: UploadFile = File(None)

):

    photo_filename = None

    if img and img.filename:

        photo_filename = f"{uuid.uuid4()}.jpg"

        photo_path = os.path.join(UPLOAD_DIR, photo_filename)

        file_bytes = await img.read()

        crop_save_uploaded_photo(file_bytes, photo_path)

    conn = get_db_connection()

    try:

        cur = conn.cursor()

        cur.execute(

            "INSERT INTO kandidat (nama, sizebaju, jeniskelamin, img, is_draft) VALUES (%s, %s, %s, %s, FALSE)",

            (nama, sizebaju, jeniskelamin, photo_filename)

        )

        conn.commit()

    finally:

        conn.close()

    return RedirectResponse(url="/app/europa/submitted", status_code=status.HTTP_303_SEE_OTHER)

@app.post("/app/europa/list/add_manual")

async def add_manual(

    nama: str = Form(...),

    nik: str = Form(None),

    sizebaju: str = Form(...),

    jeniskelamin: str = Form(...),

    lokasi: str = Form(None),

    bpo: str = Form(None),

    tipepemesanan: str = Form(None),

    img: UploadFile = File(None)

):

    photo_filename = None

    if img and img.filename:

        photo_filename = f"{uuid.uuid4()}.jpg"

        photo_path = os.path.join(UPLOAD_DIR, photo_filename)

        file_bytes = await img.read()

        crop_save_uploaded_photo(file_bytes, photo_path)

    is_dummy = (tipepemesanan == "dummy")

    final_nik = nik if nik and nik.strip() != "" else (generate_random_nik() if is_dummy else "")

    conn = get_db_connection()

    try:

        cur = conn.cursor()

        cur.execute(

            """INSERT INTO kandidat (nama, nik, sizebaju, jeniskelamin, lokasikerja, bpo, tipepemesanan, img, is_draft) 
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, FALSE)""",

            (nama, final_nik, sizebaju, jeniskelamin, lokasi, bpo, tipepemesanan, photo_filename)

        )

        conn.commit()

    finally:

        conn.close()

    return RedirectResponse(url="/app/europa/list", status_code=status.HTTP_303_SEE_OTHER)

@app.post("/app/europa/delete")

async def delete_k(nama: str = Form(...), sizebaju: str = Form(...)):

    conn = get_db_connection()

    try:

        cur = conn.cursor()

        cur.execute("SELECT img FROM kandidat WHERE nama = %s AND sizebaju = %s", (nama, sizebaju))

        row = cur.fetchone()

        uploaded_filename = row[0] if row else None

        cur.execute("DELETE FROM kandidat WHERE nama = %s AND sizebaju = %s", (nama, sizebaju))

        conn.commit()

        if uploaded_filename:

            uploaded_path = os.path.join(UPLOAD_DIR, uploaded_filename)

            if os.path.exists(uploaded_path) and uploaded_filename != "default_placeholder.png":

                try:

                    os.remove(uploaded_path)

                except Exception as e:

                    print(f"Error removing uploaded photo file: {e}")

    finally:

        conn.close()

    return RedirectResponse(url="/app/europa/list", status_code=status.HTTP_303_SEE_OTHER)

@app.post("/app/europa/list/toggle")

async def admin_toggle(action: str = Form(...), password: str = Form(None)):

    response = RedirectResponse(url="/app/europa/list", status_code=status.HTTP_303_SEE_OTHER)

    if action == "login":

        conn = get_db_connection()

        try:

            cur = conn.cursor()

            cur.execute("SELECT password FROM admins WHERE password = %s", (password,))

            row = cur.fetchone()

            db_password = row[0] if row else None

        finally:

            conn.close()

        if db_password:

            response.set_cookie(key="admin_mode", value="true", max_age=3600*24)

        else:

            return RedirectResponse(url="/app/europa/list?error=password", status_code=status.HTTP_303_SEE_OTHER)

    elif action == "logout":

        response.delete_cookie(key="admin_mode")

    return response

@app.post("/app/europa/list/preview")

async def preview_photo(

    nama: str = Form(...),

    nik: str = Form(None),

    preview_type: str = Form("dalam"),

    img: UploadFile = File(None)

):

    conn = get_db_connection()

    try:

        cur = conn.cursor()

        cur.execute("SELECT img FROM kandidat WHERE nama = %s", (nama,))

        row = cur.fetchone()

        db_img = row[0] if row else None

    finally:

        conn.close()

    photo_path = "static/default_placeholder.png"

    temp_file_to_delete = None

    if img and img.filename:

        temp_filename = f"preview_temp_{uuid.uuid4()}.jpg"

        photo_path = os.path.join(UPLOAD_DIR, temp_filename)

        file_bytes = await img.read()

        crop_save_uploaded_photo(file_bytes, photo_path)

        temp_file_to_delete = photo_path

    elif db_img:

        possible_path = os.path.join(UPLOAD_DIR, db_img)

        if os.path.exists(possible_path):

            photo_path = possible_path

    if preview_type == "luar":

        final_nik = nik if nik and nik.strip() != "" else ""

        img_io = generate_idcard_bytes(photo_path, nama, final_nik)

    else:

        if os.path.exists(photo_path) and photo_path != "static/default_placeholder.png":

            photo = Image.open(photo_path)

            photo = ImageOps.exif_transpose(photo).convert("RGBA")

        else:

            photo = Image.new("RGBA", (PHOTO_W, PHOTO_H), (200, 200, 200, 255))

        photo_cropped = photo.resize((PHOTO_W, PHOTO_H), Image.LANCZOS)

        img_io = io.BytesIO()

        photo_cropped.convert("RGB").save(img_io, "JPEG", quality=95)

        img_io.seek(0)

    if temp_file_to_delete and os.path.exists(temp_file_to_delete):

        try:

            os.remove(temp_file_to_delete)

        except Exception:

            pass

    return StreamingResponse(img_io, media_type="image/jpeg")

@app.get("/app/europa/list/view_photo")
def view_photo(img: str):
    direct_path = os.path.join(UPLOAD_DIR, img)
    if os.path.exists(direct_path) and img != "static/default_placeholder.png":
        return StreamingResponse(open(direct_path, "rb"), media_type="image/jpeg")

    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT upload_img FROM kandidathistory WHERE img = %s", (img,))
        row = cur.fetchone()
        upload_img = row[0] if row else None
    finally:
        conn.close()

    if upload_img:
        history_path = os.path.join(UPLOAD_DIR, upload_img)
        if os.path.exists(history_path):
            return StreamingResponse(open(history_path, "rb"), media_type="image/jpeg")

    card_path = os.path.join(UPLOAD_DIR_idcard, img)
    if os.path.exists(card_path):
        card = Image.open(card_path)
        photo_cropped = card.crop((PHOTO_BOX[0], PHOTO_BOX[1], PHOTO_BOX[2], PHOTO_BOX[3]))
        img_io = io.BytesIO()
        photo_cropped.convert("RGB").save(img_io, "JPEG", quality=95)
        img_io.seek(0)
        return StreamingResponse(img_io, media_type="image/jpeg")

    placeholder_path = "static/default_placeholder.png"
    if os.path.exists(placeholder_path):
        return StreamingResponse(open(placeholder_path, "rb"), media_type="image/jpeg")
    
    photo = Image.new("RGBA", (PHOTO_W, PHOTO_H), (200, 200, 200, 255))
    img_io = io.BytesIO()
    photo.convert("RGB").save(img_io, "JPEG", quality=95)
    img_io.seek(0)
    return StreamingResponse(img_io, media_type="image/jpeg")

@app.get("/app/europa/list/view_idcard")
def view_idcard(img: str):
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT nama, nik, upload_img FROM kandidathistory WHERE img = %s", (img,))
        row = cur.fetchone()
        if row:
            nama, nik, upload_img = row
        else:
            nama, nik, upload_img = None, None, None
    finally:
        conn.close()

    if nama is not None:
        photo_path = "static/default_placeholder.png"
        if upload_img:
            possible_path = os.path.join(UPLOAD_DIR, upload_img)
            if os.path.exists(possible_path):
                photo_path = possible_path

        img_io = generate_idcard_bytes(photo_path, nama, nik)
        return StreamingResponse(img_io, media_type="image/jpeg")

    possible_path = os.path.join(UPLOAD_DIR_idcard, img)
    if os.path.exists(possible_path):
        return StreamingResponse(open(possible_path, "rb"), media_type="image/jpeg")

    placeholder_path = "static/default_placeholder.png"
    if os.path.exists(placeholder_path):
        return StreamingResponse(open(placeholder_path, "rb"), media_type="image/jpeg")
    
    photo = Image.new("RGBA", (PHOTO_W, PHOTO_H), (200, 200, 200, 255))
    img_io = io.BytesIO()
    photo.convert("RGB").save(img_io, "JPEG", quality=95)
    img_io.seek(0)
    return StreamingResponse(img_io, media_type="image/jpeg")

@app.post("/app/europa/list")

async def process_list(

    nama: str = Form(...), 

    nik: str = Form(None), 

    jeniskelamin: str = Form(...),

    lokasi: str = Form(None), 

    bpo: str = Form(None), 

    tipepemesanan: str = Form(None),

    img: UploadFile = File(None),

    sizebaju: str = Form(...),

    action: str = Form("submit"),

    admin_mode: str = Cookie(None)

):      

    conn = get_db_connection()

    try:

        cur = conn.cursor()

        is_dummy = (tipepemesanan == "dummy")

        final_nik = nik if nik and nik.strip() != "" else (generate_random_nik() if is_dummy else "")

        is_admin = (admin_mode == "true")

        photo_filename = None

        if img and img.filename:

            photo_filename = f"{uuid.uuid4()}.jpg"

            photo_path = os.path.join(UPLOAD_DIR, photo_filename)

            file_bytes = await img.read()

            crop_save_uploaded_photo(file_bytes, photo_path)

        if action == "save_draft":

            cur.execute("SELECT img FROM kandidat WHERE nama = %s", (nama,))

            row = cur.fetchone()

            existing_img = row[0] if row else None

            final_img = photo_filename if photo_filename else existing_img

            if photo_filename and existing_img and existing_img != "default_placeholder.png":
                old_path = os.path.join(UPLOAD_DIR, existing_img)
                if os.path.exists(old_path):
                    try:
                        os.remove(old_path)
                    except Exception as e:
                        print(f"Error removing old draft photo: {e}")

            is_draft_val = True

            cur.execute(

                """UPDATE kandidat SET nik=%s, lokasikerja=%s, bpo=%s, tipepemesanan=%s, 
                   jeniskelamin=%s, sizebaju=%s, img=%s, is_draft=%s WHERE nama=%s""",

                (final_nik, lokasi, bpo, tipepemesanan, jeniskelamin, sizebaju, final_img, is_draft_val, nama)

            )   

            conn.commit()

            return RedirectResponse(url="/app/europa/list", status_code=status.HTTP_303_SEE_OTHER)

        if not lokasi or (tipepemesanan != "dummy" and not bpo) or not tipepemesanan:

            return RedirectResponse(url="/app/europa/list", status_code=status.HTTP_303_SEE_OTHER)

        if tipepemesanan == "dummy":

            cur.execute("SELECT img FROM kandidat WHERE nama = %s", (nama,))

            row = cur.fetchone()

            existing_img = row[0] if row else None

            final_img = photo_filename if photo_filename else existing_img

            if photo_filename and existing_img and existing_img != "default_placeholder.png":
                old_path = os.path.join(UPLOAD_DIR, existing_img)
                if os.path.exists(old_path):
                    try:
                        os.remove(old_path)
                    except Exception as e:
                        print(f"Error removing old dummy candidate photo: {e}")

            cur.execute(

                """UPDATE kandidat SET nik=%s, lokasikerja=%s, bpo=%s, tipepemesanan=%s, 
                   jeniskelamin=%s, sizebaju=%s, img=%s, is_draft=FALSE WHERE nama=%s""",

                (final_nik, lokasi, bpo, tipepemesanan, jeniskelamin, sizebaju, final_img, nama)

            )   

            conn.commit()

            return RedirectResponse(url="/app/europa/list", status_code=status.HTTP_303_SEE_OTHER)

        cur.execute("SELECT img FROM kandidat WHERE nama = %s", (nama,))

        row = cur.fetchone()

        db_img = row[0] if row else None

        final_photo_filename = photo_filename if photo_filename else db_img

        if photo_filename and db_img and db_img != "default_placeholder.png":
            old_path = os.path.join(UPLOAD_DIR, db_img)
            if os.path.exists(old_path):
                try:
                    os.remove(old_path)
                except Exception as e:
                    print(f"Error removing old candidate photo: {e}")

        if final_photo_filename:

            photo_path = os.path.join(UPLOAD_DIR, final_photo_filename)

        else:

            photo_path = "static/default_placeholder.png"

        idcard_filename = f"idcard_{uuid.uuid4()}.jpg"

        idcard_path = os.path.join(UPLOAD_DIR_idcard, idcard_filename)

        generate_idcard(photo_path, nama, final_nik, idcard_path)
        try:
            send_email(nama, final_nik, sizebaju, jeniskelamin, lokasi, bpo, tipepemesanan, idcard_path)
            print("Notification email dispatched successfully.")
        except Exception as email_err:
            print(f"Error sending email: {email_err}")

        cur.execute(

            """INSERT INTO kandidathistory(nama, nik, sizebaju, lokasikerja, bpo, tipepemesanan, img, jeniskelamin, tanggalproses, upload_img) 
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",

            (nama, final_nik, sizebaju, lokasi, bpo, tipepemesanan, idcard_filename, jeniskelamin, date.today(), final_photo_filename)

        )

        cur.execute("DELETE FROM kandidat WHERE nama = %s", (nama,))

        conn.commit()

    finally:

        conn.close()

    return RedirectResponse(url="/app/europa/list", status_code=status.HTTP_303_SEE_OTHER)

@app.get("/app/europa/list")

def klist(request: Request, admin_mode: str = Cookie(None)):

    conn = get_db_connection()

    try:

        cur = conn.cursor()

        cur.execute("SELECT MIN(id), namalokasi FROM lokasi_spil GROUP BY namalokasi ORDER BY namalokasi")

        lokasi = cur.fetchall()

        cur.execute("SELECT nama, sizebaju, jeniskelamin, nik, lokasikerja, bpo, tipepemesanan, is_draft, img FROM kandidat")

        kandidat_list = cur.fetchall()

    finally:

        conn.close()

    return templates.TemplateResponse(request, "klist.html", {

        "request": request, 

        "lokasi": lokasi, 

        "kandidat_list": kandidat_list,

        "is_admin": True

    })

@app.get("/app/europa/history")

def khistory(
    request: Request, 
    search: str = "", 
    lokasi: str = "", 
    jeniskelamin: str = "", 
    tipepemesanan: str = Query("", alias="jenispemesanan"), 
    sizebaju: str = "", 
    date_from: str = "", 
    date_to: str = "", 
    limit: str = "15", 
    page: int = 1
):

    conn = get_db_connection()

    try:

        cur = conn.cursor()

        query = "FROM kandidathistory WHERE 1=1"

        params = []

        if search:

            query += " AND (nama ILIKE %s OR nik ILIKE %s)"

            params.extend([f"%{search}%", f"%{search}%"])

        if lokasi:
            query += " AND lokasikerja = %s"
            params.append(lokasi)

        if jeniskelamin:
            query += " AND jeniskelamin = %s"
            params.append(jeniskelamin)

        if tipepemesanan:
            query += " AND tipepemesanan = %s"
            params.append(tipepemesanan)

        if sizebaju:
            query += " AND sizebaju = %s"
            params.append(sizebaju)

        if date_from:
            query += " AND tanggalproses >= %s"
            params.append(date_from)

        if date_to:
            query += " AND tanggalproses <= %s"
            params.append(date_to)

        cur.execute("SELECT COUNT(*) " + query, params)

        total_data = cur.fetchone()[0]

        limit_val = int(limit) if limit != "all" else total_data

        offset = (page - 1) * limit_val if limit != "all" else 0

        cur.execute(f"SELECT * {query} ORDER BY tanggalproses DESC LIMIT %s OFFSET %s", params + [limit_val, offset])

        kandidat_history = cur.fetchall()

    finally:

        conn.close()

    return templates.TemplateResponse(request, "khistory.html", {
	"request" : request, 
	"kandidat_history": kandidat_history, 
	"search": search,
	"lokasi": lokasi,
	"jeniskelamin": jeniskelamin,
	"tipepemesanan": tipepemesanan,
	"sizebaju": sizebaju,
	"date_from": date_from,
	"date_to": date_to, 
	"total_data": total_data, 
	"page": page, 
	"limit": limit})

@app.post("/app/europa/history/delete")

async def delete_history(

    mode: str = Form(...),

    id: int = Form(None)

):

    conn = get_db_connection()

    try:

        cur = conn.cursor()

        if mode == "single" and id is not None:

            cur.execute("SELECT img, upload_img FROM kandidathistory WHERE id = %s", (id,))

            rows = cur.fetchall()

            cur.execute("DELETE FROM kandidathistory WHERE id = %s", (id,))

        elif mode == "all":

            cur.execute("SELECT img, upload_img FROM kandidathistory")

            rows = cur.fetchall()

            cur.execute("DELETE FROM kandidathistory")

        elif mode == "dummy":

            cur.execute("SELECT img, upload_img FROM kandidathistory WHERE tipepemesanan = 'dummy'")

            rows = cur.fetchall()

            cur.execute("DELETE FROM kandidathistory WHERE tipepemesanan = 'dummy'")

        elif mode == "others":

            cur.execute("SELECT img, upload_img FROM kandidathistory WHERE tipepemesanan != 'dummy' OR tipepemesanan IS NULL")

            rows = cur.fetchall()

            cur.execute("DELETE FROM kandidathistory WHERE tipepemesanan != 'dummy' OR tipepemesanan IS NULL")

        else:

            rows = []

        conn.commit()

        for row in rows:

            idcard_filename = row[0]

            uploaded_filename = row[1]

            if idcard_filename:

                idcard_path = os.path.join(UPLOAD_DIR_idcard, idcard_filename)

                if os.path.exists(idcard_path):

                    try:

                        os.remove(idcard_path)

                    except Exception as e:

                        print(f"Error removing idcard file: {e}")

            if uploaded_filename:

                uploaded_path = os.path.join(UPLOAD_DIR, uploaded_filename)

                if os.path.exists(uploaded_path) and uploaded_filename != "default_placeholder.png":

                    try:

                        os.remove(uploaded_path)

                    except Exception as e:

                        print(f"Error removing uploaded photo file: {e}")

    finally:

        conn.close()

    return RedirectResponse(url="/app/europa/history", status_code=status.HTTP_303_SEE_OTHER)

