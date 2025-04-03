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

load_dotenv()
SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
SENDER_EMAIL = os.getenv("SENDER_EMAIL", "trivedi.abhaya10@gmail.com")

app = Flask(__name__)

from PIL import Image, ImageDraw, ImageFont
import os

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

if __name__ == '__main__':
    app.run(debug=True)