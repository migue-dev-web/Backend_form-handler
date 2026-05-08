from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import List
from fastapi.middleware.cors import CORSMiddleware
# Importaciones locales
from . import models, schemas, auth, database 
from .database import engine, get_db
from .auth import get_current_user

app = FastAPI()

# Crear tablas al iniciar
models.Base.metadata.create_all(bind=engine)




app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # En producción cambia esto por tu dominio real
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 1. AUTENTICACIÓN (LOGIN) ---

@app.post("/token", response_model=schemas.Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(models.UserDB).filter(models.UserDB.email == form_data.username).first()
    
    if not user or not auth.verify_password(form_data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Credenciales incorrectas")

    if not user.depto_rel:
        raise HTTPException(status_code=400, detail="Usuario sin departamento asignado")

    # El token lleva el código del departamento (ej: 'admin')
    access_token = auth.create_access_token(
        data={"sub": user.email, "dept": user.depto_rel.codigo}
    )
    return {"access_token": access_token, "token_type": "bearer"}

# --- 2. GESTIÓN DE DEPARTAMENTOS ---

@app.post("/departamentos", response_model=schemas.DeptoResponse)
def crear_departamento(
    depto: schemas.DeptoCreate, 
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth.get_current_user)
):
    if current_user["departamento"] != "admin":
        raise HTTPException(status_code=403, detail="No autorizado")
    
    depto.codigo = depto.codigo.lower().strip()
    db_depto = db.query(models.DepartamentoDB).filter(models.DepartamentoDB.codigo == depto.codigo).first()
    if db_depto:
        raise HTTPException(status_code=400, detail="Este código de departamento ya existe")

    nuevo_depto = models.DepartamentoDB(**depto.model_dump())
    db.add(nuevo_depto)
    db.commit()
    db.refresh(nuevo_depto)
    return nuevo_depto

@app.get("/departamentos", response_model=List[schemas.DeptoResponse])
def listar_departamentos(db: Session = Depends(get_db)):
    return db.query(models.DepartamentoDB).all()

# --- 3. GESTIÓN DE USUARIOS (CRUD) ---

@app.get("/usuarios", response_model=List[schemas.UserResponse])
def listar_usuarios(db: Session = Depends(get_db), current_user: dict = Depends(auth.get_current_user)):
    if current_user["departamento"] != "admin":
        raise HTTPException(status_code=403, detail="No autorizado")
    
    usuarios = db.query(models.UserDB).all()
    return [
        {
            "id": u.id,
            "nombre": u.nombre,
            "email": u.email,
            "departamento": u.depto_rel.nombre if u.depto_rel else "Sin asignar"
        } for u in usuarios
    ]

@app.post("/usuarios/registrar", response_model=schemas.UserResponse)
def crear_usuario(
    usuario_nuevo: schemas.UserCreate, 
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth.get_current_user)
):
    if current_user["departamento"] != "admin":
        raise HTTPException(status_code=403, detail="No autorizado")

    depto = db.query(models.DepartamentoDB).filter(models.DepartamentoDB.id == usuario_nuevo.id_departamento).first()
    if not depto:
        raise HTTPException(status_code=404, detail="El ID de departamento no existe")

    hashed_pw = auth.get_password_hash(usuario_nuevo.password)
    nuevo_db_user = models.UserDB(
        email=usuario_nuevo.email,
        nombre=usuario_nuevo.nombre,
        id_departamento=usuario_nuevo.id_departamento,
        password_hash=hashed_pw
    )
    
    db.add(nuevo_db_user)
    db.commit()
    db.refresh(nuevo_db_user)
    
    return {
        "id": nuevo_db_user.id,
        "nombre": nuevo_db_user.nombre,
        "email": nuevo_db_user.email,
        "departamento": depto.nombre
    }

@app.delete("/usuarios/{usuario_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_usuario(
    usuario_id: int, 
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth.get_current_user)
):
    if current_user["departamento"] != "admin":
        raise HTTPException(status_code=403, detail="No autorizado")

    db_user = db.query(models.UserDB).filter(models.UserDB.id == usuario_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    if db_user.email == current_user["email"]:
        raise HTTPException(status_code=400, detail="No puedes eliminarte a ti mismo")

    db.delete(db_user)
    db.commit()
    return None

# --- 4. SEGURIDAD DEL USUARIO (PASSWORD) ---

@app.put("/usuarios/me/password")
def cambiar_password(
    data: schemas.UpdatePassword,
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth.get_current_user)
):
    db_user = db.query(models.UserDB).filter(models.UserDB.email == current_user["email"]).first()

    if not auth.verify_password(data.old_password, db_user.password_hash):
        raise HTTPException(status_code=400, detail="La contraseña actual es incorrecta")

    db_user.password_hash = auth.get_password_hash(data.new_password)
    db.commit()
    return {"message": "Contraseña actualizada exitosamente"}

# --- 5. INICIO DE SISTEMA ---

@app.on_event("startup")
def crear_admin_inicial():
    db = database.SessionLocal()
    try:
        depto_admin = db.query(models.DepartamentoDB).filter(models.DepartamentoDB.codigo == "admin").first()
        if not depto_admin:
            depto_admin = models.DepartamentoDB(nombre="Administración", codigo="admin")
            db.add(depto_admin)
            db.commit()
            db.refresh(depto_admin)

        admin_existe = db.query(models.UserDB).filter(models.UserDB.email == "admin@empresa.com").first()
        if not admin_existe:
            admin = models.UserDB(
                email="admin@empresa.com",
                nombre="Administrador Global",
                id_departamento=depto_admin.id,
                password_hash=auth.get_password_hash("admin1234")
            )
            db.add(admin)
            db.commit()
    finally:
        db.close()

# --- RUTAS DE PRUEBA ---
@app.get("/perfil")
async def ver_mi_perfil(current_user: dict = Depends(get_current_user)):
    return {
        "usuario": current_user["email"],
        "departamento_tag": current_user["departamento"]
    }

# --- GESTIÓN DE FORMULARIOS ---

@app.post("/formularios", response_model=schemas.FormResponse)
def crear_formulario(
    form_in: schemas.FormCreate, 
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth.get_current_user)
):
    # Solo el administrador puede dar de alta formularios
    if current_user["departamento"] != "admin":
        raise HTTPException(status_code=403, detail="No tienes permiso para registrar formularios")
    
    # Verificar que el depto asignado exista
    depto = db.query(models.DepartamentoDB).filter(models.DepartamentoDB.id == form_in.id_departamento).first()
    if not depto:
        raise HTTPException(status_code=404, detail="El departamento asignado no existe")

    nuevo_form = models.FormularioDB(**form_in.model_dump())
    db.add(nuevo_form)
    db.commit()
    db.refresh(nuevo_form)
    
    return {
        "id": nuevo_form.id,
        "nombre": nuevo_form.nombre,
        "link": nuevo_form.link,
        "id_departamento": nuevo_form.id_departamento,
        "nombre_departamento": depto.nombre
    }

@app.get("/formularios/mis-formularios", response_model=List[schemas.FormResponse])
def obtener_mis_formularios(
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth.get_current_user)
):
    # 1. Si es ADMIN, retornar TODOS los formularios
    if current_user["departamento"] == "admin":
        query = db.query(models.FormularioDB).all()
    else:
        # 2. Si es usuario normal, filtrar por su departamento
        # Buscamos el ID del departamento del usuario actual
        user_db = db.query(models.UserDB).filter(models.UserDB.email == current_user["email"]).first()
        query = db.query(models.FormularioDB).filter(models.FormularioDB.id_departamento == user_db.id_departamento).all()

    # Formatear la respuesta
    return [
        {
            "id": f.id,
            "nombre": f.nombre,
            "link": f.link,
            "id_departamento": f.id_departamento,
            "nombre_departamento": f.depto_rel.nombre
        } for f in query
    ]