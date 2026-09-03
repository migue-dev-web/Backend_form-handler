import os
from urllib.parse import quote_plus
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# 1. Intentar obtener la URL completa (Ideal para Heroku, Render, Supabase, Railway, etc.)
DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL:
    # Corregir prefijo para compatibilidad con SQLAlchemy cuando la URL inicia con 'postgres://'
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
else:
    # 2. Si no hay DATABASE_URL, construir la URL usando variables de credenciales individuales
    db_driver = os.getenv("DB_DRIVER", "postgresql")  # Ejemplos: postgresql, mysql+pymysql, sqlite
    db_user = os.getenv("DB_USER", "")
    db_password = os.getenv("DB_PASSWORD", "")
    db_host = os.getenv("DB_HOST", "localhost")
    db_port = os.getenv("DB_PORT", "")
    db_name = os.getenv("DB_NAME", "")

    if db_user or db_name:
        # Codificar la contraseña para permitir caracteres especiales (@, #, $, %, :, /, etc.)
        password_encoded = quote_plus(db_password) if db_password else ""
        
        user_pass = f"{db_user}:{password_encoded}" if db_user else ""
        if user_pass:
            user_pass += "@"

        port_str = f":{db_port}" if db_port else ""

        DATABASE_URL = f"{db_driver}://{user_pass}{db_host}{port_str}/{db_name}"
    else:
        # Fallback a SQLite local si no se definió ninguna variable de entorno
        DATABASE_URL = "sqlite:///./sql_app.db"

engine_kwargs = {}

if "sqlite" in DATABASE_URL:
    # Configuración específica requerida para SQLite en entornos multihilo
    engine_kwargs["connect_args"] = {"check_same_thread": False}
else:
    # Para motores de producción (PostgreSQL, MySQL, SQL Server, etc.):
    # pool_pre_ping verifica si la conexión sigue viva antes de usarla (evita errores 'Server Connection Closed')
    engine_kwargs["pool_pre_ping"] = True
    engine_kwargs["pool_size"] = int(os.getenv("DB_POOL_SIZE", 10))
    engine_kwargs["max_overflow"] = int(os.getenv("DB_MAX_OVERFLOW", 20))

engine = create_engine(DATABASE_URL, **engine_kwargs)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    """
    Generador de sesión de Base de Datos para FastAPI.
    Asegura que cada Petición HTTP abra y cierre de forma limpia su conexión.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()