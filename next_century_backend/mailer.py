# mailer.py
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Change these to your Yahoo details
SMTP_HOST = "smtp.mail.yahoo.com"
SMTP_PORT = 587
SMTP_USER = "vambef7@yahoo.com"
SMTP_PASS = "keqpqqkcunudflch"

def send_signup_email(to_email, signup_link):
    subject = "Your Next Century School Account Approval"
    body = f"""
    Dear Parent,

    Congratulations! Your application has been approved.
    
    Please complete your account setup by clicking the link below:
    
    {signup_link}
    
    This link will expire in 48 hours.

    If you didn’t request this, please ignore this email.

    Regards,
    Next Century Online School
    """

    msg = MIMEMultipart()
    msg['From'] = SMTP_USER
    msg['To'] = to_email
    msg['Subject'] = subject

    msg.attach(MIMEText(body, 'plain'))

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASS)
            server.send_message(msg)
            print(f"✅ Signup email sent to {to_email}")
    except Exception as e:
        print(f"❌ Failed to send email: {e}")
