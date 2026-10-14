"""Entidades da Sprint 2, com dados fictícios para demonstração."""
from datetime import datetime
from decimal import Decimal
from sqlalchemy import Boolean, DateTime, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .database import Base


class Unidade(Base):
    __tablename__ = "unidades"
    id: Mapped[str] = mapped_column(String(20), primary_key=True)
    bloco: Mapped[str] = mapped_column(String(40))
    numero: Mapped[str] = mapped_column(String(20))
    usuarios: Mapped[list["Usuario"]] = relationship(back_populates="unidade")


class Usuario(Base):
    __tablename__ = "usuarios"
    id: Mapped[str] = mapped_column(String(20), primary_key=True)
    nome: Mapped[str] = mapped_column(String(120))
    email: Mapped[str] = mapped_column(String(180), unique=True)
    tipo: Mapped[str] = mapped_column(String(30), default="morador")
    unidade_id: Mapped[str] = mapped_column(ForeignKey("unidades.id"))
    unidade: Mapped[Unidade] = relationship(back_populates="usuarios")
    sessoes: Mapped[list["Sessao"]] = relationship(back_populates="usuario")


class Carregador(Base):
    __tablename__ = "carregadores"
    id: Mapped[str] = mapped_column(String(20), primary_key=True)
    modelo: Mapped[str] = mapped_column(String(80))
    localizacao: Mapped[str] = mapped_column(String(100))
    estado: Mapped[str] = mapped_column(String(30), default="disponivel")
    potencia_max_kw: Mapped[Decimal] = mapped_column(Numeric(8, 2))
    sessoes: Mapped[list["Sessao"]] = relationship(back_populates="carregador")


class Sessao(Base):
    __tablename__ = "sessoes"
    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    usuario_id: Mapped[str] = mapped_column(ForeignKey("usuarios.id"), index=True)
    carregador_id: Mapped[str] = mapped_column(ForeignKey("carregadores.id"), index=True)
    inicio: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    fim: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    energia_kwh: Mapped[Decimal] = mapped_column(Numeric(12, 3))
    estado: Mapped[str] = mapped_column(String(32))
    origem: Mapped[str] = mapped_column(String(32), default="simulado")
    validado: Mapped[bool] = mapped_column(Boolean, default=True)
    usuario: Mapped[Usuario] = relationship(back_populates="sessoes")
    carregador: Mapped[Carregador] = relationship(back_populates="sessoes")
