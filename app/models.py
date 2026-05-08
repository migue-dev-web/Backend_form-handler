from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from .database import Base
from sqlalchemy.orm import relationship

class DepartamentoDB(Base):
    __tablename__ = "departamentos"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, unique=True, index=True)
    codigo = Column(String, unique=True, index=True) # ej: 'admin', 'ventas'

    # Relación: Un depto tiene muchos usuarios
    usuarios = relationship("UserDB", back_populates="depto_rel")

class UserDB(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String)
    email = Column(String, unique=True, index=True)
    password_hash = Column(String)
    is_active = Column(Boolean, default=True)
    id_departamento = Column(Integer, ForeignKey("departamentos.id"))
    
    depto_rel = relationship("DepartamentoDB", back_populates="usuarios") # Aquí guardamos el tag (admin, ventas, it)

class FormularioDB(Base):
    __tablename__ = "formularios"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, index=True)
    link = Column(String)
    # Relación con el departamento
    id_departamento = Column(Integer, ForeignKey("departamentos.id"))
    
    # Relación para acceder fácilmente a los datos del depto
    depto_rel = relationship("DepartamentoDB")