from flask import Flask, render_template, request
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime
import base64
import os

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import (
    Mail, Attachment, FileContent, FileName, FileType, Disposition
)
from dotenv import load_dotenv
import pytesseract
load_dotenv()
SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
SENDER_EMAIL = os.getenv("SENDER_EMAIL", "trivedi.abhaya10@gmail.com")

app = Flask(__name__)

from PIL import Image, ImageDraw, ImageFont
import os
app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Needed for session management

def generate_certificate(name):
    TEMPLATE_PATH = "static/images/certificate_template.png"
    FONT_PATH = "/System/Library/Fonts/Supplemental/Arial.ttf"  # ✅ macOS path to Arial

    # Open certificate template
    try:
        cert = Image.open(TEMPLATE_PATH).convert("RGB")
    except FileNotFoundError:
        print(f"❌ Template not found at {TEMPLATE_PATH}")
        return None

    draw = ImageDraw.Draw(cert)

    # Load large font
    try:
        font_large = ImageFont.truetype(FONT_PATH, size=100)
    except OSError:
        print(f"❌ Could not open font resource at {FONT_PATH}")
        return None

    # Center the name text
    image_width, image_height = cert.size
    bbox = font_large.getbbox(name)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]

    x = (image_width - text_width) / 2
    y = 700  # Adjust this based on your certificate layout

    draw.text((x, y), name, font=font_large, fill="black")

    # Save the certificate
    safe_name = name.replace(" ", "_").replace("/", "_")
    filename = f"cert_{safe_name}.png"
    output_path = os.path.join("static", filename)
    cert.save(output_path)

    print(f"✅ Certificate saved at: {output_path}")
    return output_path

def send_certificate_email(recipient_email, name, cert_path):
    with open(cert_path, "rb") as f:
        encoded = base64.b64encode(f.read()).decode()

    message = Mail(
        from_email=SENDER_EMAIL,
        to_emails=recipient_email,
        subject="Books4All - Certificate of Appreciation",
        html_content=f"""
        <p>Dear {name},</p>
        <p>Thank you for your generous donation to <strong>Books4All</strong>!</p>
        <p>Please find your certificate of appreciation attached.</p>
        <p>Warm regards,<br>Books4All Team</p>
        """
    )

    attachment = Attachment()
    attachment.file_content = FileContent(encoded)
    attachment.file_type = FileType("image/png")
    attachment.file_name = FileName("Books4All_Certificate.png")
    attachment.disposition = Disposition("attachment")
    message.attachment = attachment

    try:
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        response = sg.send(message)
        print(f"✅ Email sent to {recipient_email} | Status: {response.status_code}")
    except Exception as e:
        print(f"❌ Error sending email: {str(e)}")
def extract_fields(image_path):
    import pytesseract
    from PIL import Image

    img = Image.open(image_path)
    raw_text = pytesseract.image_to_string(img)

    title = ""
    author = ""
    for line in raw_text.split("\n"):
        if "by" in line.lower():
            parts = line.split("by")
            title = parts[0].strip()
            author = parts[1].strip() if len(parts) > 1 else ""

    return {
        "title": title,
        "author": author,
        "raw": raw_text
    }
def predict_genre(text):
    text = text.lower()
    if "math" in text:
        return "Mathematics"
    elif "history" in text:
        return "History"
    elif "science" in text:
        return "Science"
    elif "grammar" in text or "language" in text:
        return "Language"
    elif "biology" in text or "chemistry" in text:
        return "Biology/Chemistry"
    else:
        return "General"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/home')
def home():
    return render_template('home.html')

@app.route('/form', methods=['GET', 'POST'])
def form():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']

        cert_path = generate_certificate(name)
        send_certificate_email(email, name, cert_path)

        return f"🎉 Certificate sent to {email}!"
    return render_template('form.html')
@app.route('/donate', methods=['GET', 'POST'])
def donate_combined():
    data = {}
    if request.method == 'POST':
        file = request.files['image']
        if file:
            save_dir = "static/images"
            os.makedirs(save_dir, exist_ok=True)
            path = os.path.join(save_dir, file.filename)
            file.save(path)

            data = extract_fields(path)
            data["genre"] = predict_genre(data.get("raw", ""))

        # Optional: Save other form values here for database entry

    return render_template("donate.html", data=data)
@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')
@app.route('/booksearch')
def booksearch():
    return render_template('booksearch.html')

if __name__ == '__main__':
    app.run(debug=True)