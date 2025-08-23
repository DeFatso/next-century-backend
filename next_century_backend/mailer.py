# mailer.py
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Change these to your Yahoo details
SMTP_HOST = "smtp.mail.yahoo.com"
SMTP_PORT = 587
SMTP_USER = "vambef7@yahoo.com"
SMTP_PASS = "keqpqqkcunudflch"

def send_signup_email(parent_email, child_name, signup_link):
    """
    Send signup email to parent with registration link
    
    Args:
        parent_email (str): Parent's email address
        child_name (str): Child's name for personalization
        signup_link (str): Registration link with token
    """
    try:
        # Your email sending implementation here
        print(f"📧 Sending signup email to: {parent_email}")
        print(f"   Child: {child_name}")
        print(f"   Signup link: {signup_link}")
        
        # Example using smtplib (adjust based on your actual implementation):
        # msg = MIMEText(f"Hello! Click here to complete registration for {child_name}: {signup_link}")
        # msg['Subject'] = f"Complete {child_name}'s Registration"
        # msg['From'] = 'your-email@school.com'
        # msg['To'] = parent_email
        
        # server.send_message(msg)
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to send email: {e}")
        return False