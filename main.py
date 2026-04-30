from fastapi import FastAPI, Request, Form, status, File, UploadFile
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from pythontopsql import get_db_connection
from PIL import Image, ImageDraw, ImageFont
import os
import uuid
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from datetime import date

# ─── ID Card Generation Config ───────────────────────────────────────────────
TEMPLATE_PATH = "static/template.png"

# Photo box pixel coordinates on the template (1993 x 3138 px)
PHOTO_BOX = (593, 1072, 1398, 2275)   # left, top, right, bottom
PHOTO_W   = PHOTO_BOX[2] - PHOTO_BOX[0]  # 805 px
PHOTO_H   = PHOTO_BOX[3] - PHOTO_BOX[1]  # 762 px

CARD_CENTER_X   = 996    # horizontal centre of the card
NAME_Y_CENTER   = 2500   # vertical centre for name text
NIK_Y_CENTER    = 2715   # vertical centre for NIK text

FONT_BOLD = "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"
FONT_REG  = "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"   


def generate_idcard(photo_path: str, name: str, nik: str, output_path: str) -> None:
    """Composite employee photo + text onto the ID card template and save."""
    # Load template
    card = Image.open(TEMPLATE_PATH).convert("RGBA")

    # --- Paste employee photo ---
    photo = Image.open(photo_path).convert("RGBA")
    pw, ph = photo.size
    box_aspect   = PHOTO_W / PHOTO_H
    photo_aspect = pw / ph

    if photo_aspect > box_aspect:
        # Photo wider than box — scale by height
        new_h = PHOTO_H
        new_w = int(PHOTO_H * photo_aspect)
    else:
        # Photo taller than box — scale by width
        new_w = PHOTO_W
        new_h = int(PHOTO_W / photo_aspect)

    photo_resized = photo.resize((new_w, new_h), Image.LANCZOS)
    crop_left = (new_w - PHOTO_W) // 2
    crop_top  = (new_h - PHOTO_H) // 2
    photo_cropped = photo_resized.crop(
        (crop_left, crop_top, crop_left + PHOTO_W, crop_top + PHOTO_H)
    )
    card.paste(photo_cropped, (PHOTO_BOX[0], PHOTO_BOX[1]))

    # --- Draw text ---
    draw = ImageDraw.Draw(card)

    try:
        font_name = ImageFont.truetype(FONT_BOLD, 135)
        font_rest = ImageFont.truetype(FONT_REG, 135)
        font_nik  = ImageFont.truetype(FONT_BOLD,  100)
        print("FONT LOADED SUCCESSFULLY")
    except IOError:
        font_name = ImageFont.load_default()
        font_nik  = font_name
        print("FONT not LOADED SUCCESSFULLY")

    # Name (bold, centered)
    name_upper = name.upper()
    parts = name_upper.split(" ",1)
    
    first = parts[0]
    rest = parts[1] if len(parts) > 1 else ""
    
    bbox_first = draw.textbbox((0, 0), first, font=font_name)
    w_first = bbox_first[2] - bbox_first[0]
    
    bbox_rest = draw.textbbox((0, 0), " "+ rest, font= font_rest)
    w_rest = bbox_rest[2] - bbox_rest[0]
    
    total_width = w_first + w_rest
    
    x_start = CARD_CENTER_X - total_width // 2
    y = NAME_Y_CENTER
    
    draw.text((x_start, y), first, font=font_name, fill="black")
    
    draw.text((x_start + w_first, y), " " + rest, font=font_rest, fill="black")

    # NIK — clear the "<NIK>" placeholder, then draw real NIK
    bbox2 = draw.textbbox((0, 0), nik, font=font_nik)
    tw2 = bbox2[2] - bbox2[0]
    th2 = bbox2[3] - bbox2[1]
    draw.text(
        (CARD_CENTER_X - tw2 // 2, NIK_Y_CENTER - th2 // 2),
        nik,
        font=font_nik,
        fill="black",
    )

    # Save as JPEG
    card.convert("RGB").save(output_path, "JPEG", quality=95)
# ─────────────────────────────────────────────────────────────────────────────

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

UPLOAD_DIR ="static/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

UPLOAD_DIR_idcard ="static/idcardphoto"
os.makedirs(UPLOAD_DIR_idcard, exist_ok=True)

templates = Jinja2Templates(directory="templates")

@app.get("/kandidat/form")
def kform(request: Request):
    return templates.TemplateResponse(request, "kform.html")

@app.get("/kandidat/submited")
def kform(request: Request):
    return templates.TemplateResponse(request, "ksubmited.html")

@app.post("/kandidat/form")
async def submit_kform(nama: str = Form(...), sizebaju: str = Form(...), jeniskelamin: str = Form(...)):
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("INSERT INTO kandidat (nama, sizebaju, jeniskelamin) VALUES (%s, %s, %s)", (nama, sizebaju, jeniskelamin))
        conn.commit()
        cur.close()
    except Exception as error:
        print(f"Error inserting to database: {error}")
        conn.rollback()
    finally:
        conn.close()
    
    return RedirectResponse(url="/kandidat/submited", status_code=status.HTTP_303_SEE_OTHER)

@app.post("/kandidat/delete")
async def submit_klist(
  nama: str = Form(...),
  sizebaju: str = Form(...)  
):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            "DELETE FROM kandidat WHERE nama = %s AND sizebaju = %s",
            (nama,sizebaju)
        )
        conn.commit()
        cur.close()
    except Exception as error:
        print(f"Error Inserting to Database: {error}")
        conn.rollback()
    finally:
        conn.close()
        
    return RedirectResponse(url="/kandidat/list", status_code=status.HTTP_303_SEE_OTHER)
   

@app.post("/kandidat/list")
async def submit_klist(
    nama: str = Form(...), 
    nik: str = Form(...), 
    jeniskelamin: str = Form(...),
    lokasi: str = Form(...), 
    bpo: str = Form(...), 
    tipepemesanan: str = Form(...),
    img: UploadFile = File(...),
    sizebaju: str = Form(...)
):      
    conn = get_db_connection()
    try:
        # Save uploaded photo
        ext = img.filename.split(".")[-1] if "." in img.filename else "jpg"
        photo_filename = f"{uuid.uuid4()}.{ext}"
        photo_path = os.path.join(UPLOAD_DIR, photo_filename)
        with open(photo_path, "wb") as f:
            f.write(await img.read())

        # Generate ID card
        idcard_filename = f"idcard_{uuid.uuid4()}.jpg"
        idcard_path = os.path.join(UPLOAD_DIR_idcard, idcard_filename)
        generate_idcard(
            photo_path=photo_path,
            name=nama,
            nik=nik,
            output_path=idcard_path,
        )
        
        send_email(nama,nik,sizebaju,jeniskelamin,lokasi, bpo, tipepemesanan, idcard_path)

        today = date.today()
        
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO kandidathistory(nama, nik, sizebaju, lokasikerja, bpo, tipepemesanan, img, jeniskelamin, tanggalproses) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
            (nama, nik, sizebaju, lokasi, bpo, tipepemesanan, idcard_filename, jeniskelamin, today)
        )
        cur.execute(
            "DELETE FROM kandidat WHERE nama = %s AND sizebaju = %s",
            (nama, sizebaju)
        )
        conn.commit()
        cur.close()
    except Exception as error:
        print(f"Error Inserting to Database: {error}")
        conn.rollback()
    finally:
        conn.close()

    return RedirectResponse(url="/kandidat/list", status_code=status.HTTP_303_SEE_OTHER)

@app.get("/kandidat/list")
def klist(request: Request):
    conn = get_db_connection()

    try:
        cur = conn.cursor()
        cur.execute("SELECT id, namalokasi FROM lokasi_spil ORDER BY namalokasi")
        lokasi = cur.fetchall()

        cur.execute("SELECT nama, sizebaju, jeniskelamin FROM kandidat")
        kandidat_list = cur.fetchall()

        conn.commit()
        cur.close()
    except Exception as error:
        print(f"Error get database: {error}")
        conn.rollback()
    finally:
        conn.close()

    return templates.TemplateResponse(request, "klist.html",
                                      {
                                          "request": request, 
                                          "lokasi": lokasi,
                                          "kandidat_list": kandidat_list
                                          }
                                      )
    
@app.get("/kandidat/history")
def khistory(
    request: Request, 
    search: str = "",
    lokasi: str = "",
    jeniskelamin: str = "",
    jenispemesanan: str = "",
    sizebaju: str = "",
    date_from: str = "",
    date_to: str = "",
    limit: str = "15",
    page: int = 1
    ):
    
    conn = get_db_connection()
    total_data = 0
    
    try:
        cur = conn.cursor()
        
        query = "FROM kandidathistory WHERE 1=1"
        params = []
                
        if search:
            query += " AND (nama ILIKE %s OR nik ILIKE %s OR sizebaju ILIKE %s OR lokasikerja ILIKE %s OR bpo ILIKE %s OR tipepemesanan ILIKE %s OR jeniskelamin ILIKE %s)"
            params.extend([f"%{search}%", f"%{search}%", f"%{search}%", f"%{search}%", f"%{search}%", f"%{search}%", f"%{search}%"])
        
        if lokasi:
            query += " AND lokasikerja = %s"
            params.append(lokasi)
        
        if jeniskelamin:
            query += " AND jeniskelamin = %s"
            params.append(jeniskelamin)
            
        if jenispemesanan:
            query += " AND tipepemesanan = %s"
            params.append(jenispemesanan) 
        
        if sizebaju:
            query += " AND sizebaju = %s"
            params.append(sizebaju)
        
        if date_from:
            query += " AND tanggalproses >= %s"
            params.append(date_from)

        if date_to:
            query += " AND tanggalproses <= %s"
            params.append(date_to)
            
        # --- COUNT TOTAL ---
        cur.execute("SELECT COUNT(*) " + query, params)
        total_data = cur.fetchone()[0]

        # --- PAGINATION ---
        if limit != "all":
            limit_int = int(limit)
            offset = (page - 1) * limit_int

            query_final = "SELECT * " + query + " ORDER BY tanggalproses DESC LIMIT %s OFFSET %s"
            params_final = params + [limit_int, offset]
        else:
            query_final = "SELECT * " + query + " ORDER BY tanggalproses DESC"
            params_final = params

        cur.execute(query_final, params_final)
        kandidat_history = cur.fetchall()
                       
        cur.close()
    except Exception as error:
        print(f"Error get database: {error}")
        conn.rollback()
        kandidat_history = []
    finally:
        conn.close()
    return templates.TemplateResponse(request, "khistory.html",
                                      {
                                          "request" : request,
                                          "kandidat_history": kandidat_history,
                                          "search": search,
                                          "lokasi": lokasi,
                                          "jeniskelamin": jeniskelamin,
                                          "tipe": jenispemesanan,
                                          "date_from": date_from,
                                          "date_to": date_to,
                                          "limit":limit,
                                          "page": page,
                                          "total_data": total_data
                                      })
    
def send_email(nama, nik, sizebaju, jeniskelamin, lokasi, bpo, tipepemesanan, idcard_path):
    msg = MIMEMultipart()
    msg ["Subject"] = f"ID Card Karyawan Baru : {nama} ({sizebaju}) - {lokasi}"
    msg ["From"] = "c14180198@alumni.petra.ac.id"
    msg ["To"] = "thomasnikijuluw13@gmail.com"
    
    body = f"""
        <h2>Dear Pak Haryo,</h2>
    
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
    

    
    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login("c14180198@alumni.petra.ac.id", "xtfn hxwo rozp aqug")
        print("Masuk Email")
        server.send_message(msg)