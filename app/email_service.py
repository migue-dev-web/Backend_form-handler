import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

load_dotenv()

SMTP_SERVER = os.getenv("SMTP_SERVER") # O el de tu proveedor
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SMTP_USER = os.getenv("SMTP_USER")                      # Tu correo/usuario registrado
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")              # Tu contraseña de aplicación

def enviar_correo(destinatario: str, asunto: str, cuerpo_html: str):
    if not SMTP_USER or not SMTP_PASSWORD:
        print("Configuración de SMTP incompleta. Correo no enviado.")
        return False

    msg = MIMEMultipart("alternative")
    msg["Subject"] = asunto
    msg["From"] = SMTP_USER
    msg["To"] = destinatario

    # Adjuntar el diseño en HTML
    parte_html = MIMEText(cuerpo_html, "html")
    msg.attach(parte_html)

    try:
        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as server:
            
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(SMTP_USER, destinatario, msg.as_string())
        return True
    except Exception as e:
        print(f"Error al enviar correo a {destinatario}: {e}")
        return False