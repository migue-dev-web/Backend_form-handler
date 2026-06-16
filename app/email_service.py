
import os
import requests
from dotenv import load_dotenv

load_dotenv()


BREVO_API_KEY = os.getenv("BREVO_API_KEY")
REMITENTE_CORREO = os.getenv("SMTP_USER") 

def enviar_correo(destinatario: str, asunto: str, cuerpo_html: str):
    if not BREVO_API_KEY or not REMITENTE_CORREO:
        print("Configuración de la API incompleta. Correo no enviado.")
        return False

    url_api = "https://api.brevo.com/v3/smtp/email"
    
    # Encabezados obligatorios para autenticarse con Brevo
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "api-key": BREVO_API_KEY
    }

    # Estructura del JSON que pide la documentación de Brevo
    payload = {
        "sender": {"email": REMITENTE_CORREO, "name": "Sistema de Formulario"},
        "to": [{"email": destinatario}],
        "subject": asunto,
        "htmlContent": cuerpo_html
    }

    try:
       
        response = requests.post(url_api, json=payload, headers=headers)
        
        if response.status_code in [200, 201]:
            return True
        else:
            print(f"Brevo rechazó el correo: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"Error de conexión al enviar correo vía API: {e}")
