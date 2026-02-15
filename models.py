from sqlalchemy import (
    Column, Integer, String, Float, ForeignKey, DateTime, Text, UniqueConstraint, Index
)
from sqlalchemy.orm import relationship
from database import Base
import datetime

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    name = Column(String, nullable=False)
    year = Column(Integer)                     # año de cursada (1-6)
    current_catedra = Column(String)           # cátedra actual de arquitectura
    role = Column(String, default="student")   # student, ayudante, profesor, admin
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    posts = relationship("Post", back_populates="author", cascade="all, delete-orphan")
    likes = relationship("Like", back_populates="user", cascade="all, delete-orphan")
    user_tps = relationship("UserTP", back_populates="user", cascade="all, delete-orphan")
    ratings = relationship("Rating", back_populates="user", cascade="all, delete-orphan")

class Subject(Base):
    __tablename__ = "subjects"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    year = Column(Integer, nullable=False)      # año al que pertenece (1-6)

    tps = relationship("TP", back_populates="subject", cascade="all, delete-orphan")
    catedras = relationship("Catedra", back_populates="subject", cascade="all, delete-orphan")
    posts = relationship("Post", back_populates="subject")
    resources = relationship("Resource", back_populates="subject", cascade="all, delete-orphan")

class Catedra(Base):
    __tablename__ = "catedras"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    subject_id = Column(Integer, ForeignKey("subjects.id"), nullable=False, index=True)

    subject = relationship("Subject", back_populates="catedras")
    ratings = relationship("Rating", back_populates="catedra", cascade="all, delete-orphan")

class TP(Base):
    __tablename__ = "tps"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)       # ej. "TP1"
    subject_id = Column(Integer, ForeignKey("subjects.id"), nullable=False, index=True)
    order = Column(Integer)                      # para ordenamiento

    subject = relationship("Subject", back_populates="tps")
    user_tps = relationship("UserTP", back_populates="tp", cascade="all, delete-orphan")

    __table_args__ = (UniqueConstraint("subject_id", "order", name="_tp_subject_order_uc"),)

class UserTP(Base):
    __tablename__ = "user_tps"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    tp_id = Column(Integer, ForeignKey("tps.id"), nullable=False, index=True)
    state = Column(String, default="Pendiente")  # Pendiente, Entregado, Aprobado
    grade = Column(Float, nullable=True)         # nota (opcional)

    user = relationship("User", back_populates="user_tps")
    tp = relationship("TP", back_populates="user_tps")

    __table_args__ = (UniqueConstraint("user_id", "tp_id", name="_user_tp_uc"),)

class Post(Base):
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    subject_id = Column(Integer, ForeignKey("subjects.id"), nullable=False, index=True)
    image_path = Column(String, nullable=False)   # ruta relativa dentro de uploads/
    caption = Column(Text)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, index=True)

    author = relationship("User", back_populates="posts")
    subject = relationship("Subject", back_populates="posts")
    likes = relationship("Like", back_populates="post", cascade="all, delete-orphan")

class Like(Base):
    __tablename__ = "likes"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    post_id = Column(Integer, ForeignKey("posts.id"), nullable=False, index=True)

    user = relationship("User", back_populates="likes")
    post = relationship("Post", back_populates="likes")

    __table_args__ = (UniqueConstraint("user_id", "post_id", name="_user_post_like_uc"),)

class Resource(Base):
    __tablename__ = "resources"

    id = Column(Integer, primary_key=True)
    subject_id = Column(Integer, ForeignKey("subjects.id"), nullable=False, index=True)
    title = Column(String, nullable=False)
    description = Column(Text)
    file_path = Column(String, nullable=True)    # opcional para adjuntar archivo
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    subject = relationship("Subject", back_populates="resources")

class Rating(Base):
    __tablename__ = "ratings"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    catedra_id = Column(Integer, ForeignKey("catedras.id"), nullable=False, index=True)
    rating = Column(Integer, nullable=False)     # 1 a 5
    comment = Column(Text)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    user = relationship("User", back_populates="ratings")
    catedra = relationship("Catedra", back_populates="ratings")

    __table_args__ = (UniqueConstraint("user_id", "catedra_id", name="_user_catedra_rating_uc"),)
