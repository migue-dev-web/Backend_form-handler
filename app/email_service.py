
import os
import requests
from dotenv import load_dotenv

load_dotenv()

GOOGLE_SCRIPT_URL = os.getenv("GOOGLE_SCRIPT_URL")

def enviar_correo(destinatario: str, asunto: str, cuerpo_html: str):
    if not GOOGLE_SCRIPT_URL:
        print("Variable GOOGLE_SCRIPT_URL no configurada. Correo abortado.")
        return False


    # Estructura del JSON que pide la documentación de Brevo
    payload = {
        "destinatario": destinatario,
        "subject": asunto,  # El script busca data.asunto, cámbialo a "asunto" para que coincida con el js anterior
        "asunto": asunto,
        "cuerpo_html": cuerpo_html
    }

    try:
       
        response = requests.post(GOOGLE_SCRIPT_URL, json=payload)
        
        resultado = response.json()
        if response.status_code == 200:
            resultado = response.json()
            if resultado.get("status") == "success":
                return True
            else:
                print(f"Google Apps Script reportó un error: {resultado.get('message')}")
                return False
        else:
            print(f"Falló la conexión con Google. Status code: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"Error al conectar con Google Apps Script: {e}")
        return False