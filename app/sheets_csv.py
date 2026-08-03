import csv, io
from urllib.request import urlopen
import pandas as pd
from sqlalchemy.orm import Session
from fastapi import HTTPException
import app.models as models


def leer_respuestas(sheet_id: str):
    """Devuelve (headers, rows) de la primera pestaña del spreadsheet público."""
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"
    with urlopen(url, timeout=10) as resp:
        text = resp.read().decode("utf-8")
    rows = list(csv.reader(io.StringIO(text)))
    if not rows:
        return [], []
    headers = rows[0]
    body = rows[1:]
    body = [r + [""] * (len(headers) - len(r)) for r in body]
    return headers, body

def obtener_encabezados_formulario(form_id: int, db: Session) -> list[str]:
    form = db.query(models.FormularioDB).filter(models.FormularioDB.id == form_id).first()
    if not form or not form.sheet_id:
        raise HTTPException(status_code=404, detail="Formulario no encontrado o sin Sheet ID asignado.")
    
    url_csv = f"https://docs.google.com/spreadsheets/d/{form.sheet_id}/export?format=csv"
    try:
        df_header = pd.read_csv(url_csv, nrows=0)

        columnas = df_header.columns.tolist()
        encabezados_filtrados = [
            col for col in columnas 
            if col.strip() != "Marca temporal"
        ]

        return encabezados_filtrados

    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al leer el CSV de Google Sheets: {str(e)}")