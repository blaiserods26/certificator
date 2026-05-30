import smtplib
import ssl
from email.message import EmailMessage
import pandas as pd
import os

def send_emails(csv_path, cert_dir, sender_email, app_password, subject, body):
    """
    Sends emails to participants based on CSV and generated certificates.
    Returns: (success_count, error_count, log_list)
    """
    if not os.path.exists(csv_path):
        return 0, 0, ["CSV file not found."]

    try:
        df = pd.read_csv(csv_path)
    except Exception as e:
        return 0, 0, [f"Error reading CSV: {e}"]

    context = ssl.create_default_context()
    
    success_count = 0
    error_count = 0
    logs = []

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
            server.login(sender_email, app_password)
            
            for _, row in df.iterrows():
                name = str(row.get("name", "")).strip()
                email = str(row.get("email", "")).strip()
                
                if not email or "@" not in email:
                    logs.append(f"Skipping invalid email for {name}: {email}")
                    error_count += 1
                    continue

                # Find certificate
                safe_name = "".join(x for x in name if x.isalnum() or x in (' ', '_', '-')).replace(" ", "_")
                cert_filename = f"{safe_name}.pdf"
                cert_path = os.path.join(cert_dir, cert_filename)
                
                if not os.path.exists(cert_path):
                     # Try loosely matching? No, stick to strict naming for now.
                     logs.append(f"Certificate not found for {name}: {cert_path}")
                     error_count += 1
                     continue

                msg = EmailMessage()
                msg["Subject"] = subject
                msg["From"] = sender_email
                msg["To"] = email
                
                # Simple template replacement
                email_body = body.replace("{name}", name)
                msg.set_content(email_body)

                with open(cert_path, "rb") as f:
                    file_data = f.read()
                    
                msg.add_attachment(file_data, maintype="application", subtype="pdf", filename=cert_filename)

                try:
                    server.send_message(msg)
                    logs.append(f"Sent to {email}")
                    success_count += 1
                except Exception as e:
                    logs.append(f"Failed to send to {email}: {e}")
                    error_count += 1

    except Exception as e:
        return success_count, error_count, logs + [f"SMTP Error: {e}"]

    return success_count, error_count, logs
