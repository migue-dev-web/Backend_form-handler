from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy.orm import Session
from app.database import SessionLocal  # Importa tu generador de sesiones local
from app import models, email_service

def evaluar_y_notificar_formularios():
    db: Session = SessionLocal()
    ahora = datetime.utcnow()
    
    try:
        # --- CASO A: NOTIFICACIÓN DE APERTURA ---
        # Formularios cuya fecha_inicio ya pasó, pero no se ha mandado el aviso
        programaciones_apertura = db.query(models.FormScheduleDB).filter(
            models.FormScheduleDB.fecha_inicio <= ahora,
            models.FormScheduleDB.fecha_fin > ahora,
            models.FormScheduleDB.aviso_apertura_enviado == False
        ).all()

        for prog in programaciones_apertura:
            form = prog.formulario
            # Consumir usuarios relacionados al departamento del formulario
            usuarios = db.query(models.UsuarioDB).filter(models.UsuarioDB.id_departamento == form.id_departamento).all()
            
            for usuario in usuarios:
                html = f"<h3>¡Hola, {usuario.nombre}!</h3><p>El formulario <b>{form.nombre}</b> ya está disponible para su llenado.</p>"
                exito = email_service.enviar_correo(usuario.email, f"Apertura: {form.nombre}", html)
                
                # Registrar en el log de notificaciones
                log = models.NotificationLogDB(
                    id_formulario=form.id,
                    usuario_destino=usuario.email,
                    tipo_notificacion="APERTURA",
                    estado="EXITOSO" if exito else "FALLIDO"
                )
                db.add(log)
            
            # Marcar como enviado para no repetir en el próximo ciclo
            prog.aviso_apertura_enviado = True
            db.commit()

        # --- CASO B: RECORDATORIO DE CIERRE ---
        # Formularios que cierran en menos de 24 horas y no se ha enviado aviso de cierre
        limite_cierre = ahora + timedelta(hours=24)
        programaciones_cierre = db.query(models.FormScheduleDB).filter(
            models.FormScheduleDB.fecha_fin <= limite_cierre,
            models.FormScheduleDB.fecha_fin > ahora,
            models.FormScheduleDB.aviso_cierre_enviado == False
        ).all()

        for prog in programaciones_cierre:
            form = prog.formulario
            usuarios = db.query(models.UsuarioDB).filter(models.UsuarioDB.id_departamento == form.id_departamento).all()
            
            for usuario in usuarios:
                html = f"<h3>Recordatorio Urgente</h3><p>El formulario {form.nombre} cerrará pronto: {prog.fecha_fin}. Por favor, complétalo.</p>"
                exito = email_service.enviar_correo(usuario.email, f"Recordatorio de Cierre: {form.nombre}", html)
                
                log = models.NotificationLogDB(
                    id_formulario=form.id,
                    usuario_destino=usuario.email,
                    tipo_notificacion="RECORDATORIO_CIERRE",
                    estado="EXITOSO" if exito else "FALLIDO"
                )
                db.add(log)
                
            prog.aviso_cierre_enviado = True
            db.commit()

    except Exception as e:
        print(f"Error en el Scheduler: {e}")
    finally:
        db.close()

# Inicializar el Scheduler para que corra en segundo plano
scheduler = BackgroundScheduler()
# Evalúa la función cada 10 minutos
scheduler.add_job(evaluar_y_notificar_formularios, 'interval', minutes=10)