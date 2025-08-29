import os
from flask import Flask, request, jsonify
from flask_cors import CORS
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

app = Flask(__name__)
CORS(app)

# === CONFIG (use env vars for safety) ===
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SENDER_EMAIL = os.getenv("SENDER_EMAIL", "rajp95146@gmail.com")        # your gmail
SENDER_PASSWORD = os.getenv("SENDER_PASSWORD", "faxd pfog muos obdi")   # gmail app password
RECEIVER_EMAIL = os.getenv("RECEIVER_EMAIL", "rajpritam.0518@gmail.com")  # admin/you

# Display names as you wanted
DISPLAY_NAME = "Pritam"

def build_admin_message(name, email, phone, subject, message):
    msg = MIMEMultipart("alternative")
    # From and To with display names
    msg["From"] = f"{DISPLAY_NAME} <{SENDER_EMAIL}>"
    msg["To"] = f"{DISPLAY_NAME} <{RECEIVER_EMAIL}>"
    msg["Subject"] = f"📩 New Contact Form Submission: {subject}"

    plain_body = f"""Hello Admin,

You have received a new contact form submission.

Name   : {name}
Email  : {email}
Phone  : {phone if phone else 'Not provided'}
Subject: {subject}

Message:
{message}

-------------------------
This email was automatically sent by your website contact system.
"""
    html_body = f"""
    <html>
      <body style="font-family: Arial, sans-serif; background:#f6f8fb; padding:20px;">
        <div style="max-width:700px;margin:auto;background:#ffffff;border-radius:8px;box-shadow:0 2px 8px rgba(0,0,0,0.08);overflow:hidden;">
          <div style="background:#e11d48;color:#fff;padding:14px 18px;font-size:18px;">📩 New Contact Form Submission</div>
          <div style="padding:18px;color:#333;">
            <p><strong>Name:</strong> {name}</p>
            <p><strong>Email:</strong> {email}</p>
            <p><strong>Phone:</strong> {phone if phone else 'Not provided'}</p>
            <p><strong>Subject:</strong> {subject}</p>
            <hr>
            <p><strong>Message</strong></p>
            <div style="border-left:3px solid #e11d48;padding-left:10px;color:#444;">{message}</div>
            <hr>
            <p style="font-size:12px;color:#777;">This email was automatically sent by your website contact system.</p>
          </div>
        </div>
      </body>
    </html>
    """

    msg.attach(MIMEText(plain_body, "plain"))
    msg.attach(MIMEText(html_body, "html"))
    return msg

def build_reply_message(name, to_email, original_subject, original_message):
    reply = MIMEMultipart("alternative")
    reply["From"] = f"{DISPLAY_NAME} <{SENDER_EMAIL}>"
    reply["To"] = f"{name} <{to_email}>"
    reply["Subject"] = f"Re: {original_subject} — Thanks for contacting us"

    plain = f"""Hello {name},

Thank you for contacting us. We have received your message:

"{original_message}"

We will get back to you shortly.

Best regards,
{DISPLAY_NAME}
"""
    html = f"""
    <html><body style="font-family: Arial, sans-serif; padding:18px;">
      <h2 style="color:#e11d48;">Thank you, {name}!</h2>
      <p>We have received your message:</p>
      <blockquote style="border-left:3px solid #e11d48;padding-left:10px;color:#444;">
        {original_message}
      </blockquote>
      <p>We will get back to you shortly.</p>
      <p>Best regards,<br><strong>{DISPLAY_NAME}</strong></p>
    </body></html>
    """

    reply.attach(MIMEText(plain, "plain"))
    reply.attach(MIMEText(html, "html"))
    return reply

@app.route('/contact', methods=['POST'])
def contact():
    try:
        # Frontend sends FormData, so use request.form
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        phone = request.form.get('phone', '').strip()
        subject = request.form.get('subject', '').strip()
        message = request.form.get('message', '').strip()

        if not name or not email or not subject or not message:
            return jsonify({"status": "error", "message": "Missing required fields"}), 400

        # Build messages
        admin_msg = build_admin_message(name, email, phone, subject, message)
        reply_msg = build_reply_message(name, email, subject, message)

        # Send admin email
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.sendmail(SENDER_EMAIL, RECEIVER_EMAIL, admin_msg.as_string())

        # Send auto-reply to user
        try:
            with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
                server.starttls()
                server.login(SENDER_EMAIL, SENDER_PASSWORD)
                server.sendmail(SENDER_EMAIL, email, reply_msg.as_string())
        except Exception as e:
            # auto-reply failure shouldn't block main success — just log and continue
            print("Auto-reply failed:", e)

        return jsonify({"status": "success", "message": "Message sent successfully!"}), 200

    except Exception as e:
        print("Error in /contact:", e)
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    # For local testing
    app.run(host='0.0.0.0', port=5000, debug=True)