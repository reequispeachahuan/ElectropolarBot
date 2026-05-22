from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Date, DateTime, ForeignKey, Numeric, String, Text, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Opportunity(Base):
    __tablename__ = "opportunities"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    source: Mapped[str] = mapped_column(String(120), index=True)
    seace_code: Mapped[str | None] = mapped_column(String(120), unique=True)
    title: Mapped[str] = mapped_column(Text)
    description: Mapped[str | None] = mapped_column(Text)
    entity_name: Mapped[str | None] = mapped_column(String(255), index=True)
    region: Mapped[str | None] = mapped_column(String(120), index=True)
    object_type: Mapped[str | None] = mapped_column(String(60))
    procedure_type: Mapped[str | None] = mapped_column(String(120))
    estimated_amount: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))
    publication_date: Mapped[date | None] = mapped_column(Date)
    deadline: Mapped[date | None] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(40), default="nueva", index=True)
    priority: Mapped[str] = mapped_column(String(40), default="baja", index=True)
    score: Mapped[int] = mapped_column(default=0)
    seace_url: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    documents: Mapped[list[Document]] = relationship(back_populates="opportunity", cascade="all, delete-orphan")
    matches: Mapped[list[Match]] = relationship(back_populates="opportunity", cascade="all, delete-orphan")
    evaluations: Mapped[list[Evaluation]] = relationship(back_populates="opportunity", cascade="all, delete-orphan")
    alerts: Mapped[list[Alert]] = relationship(back_populates="opportunity", cascade="all, delete-orphan")


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    opportunity_id: Mapped[str] = mapped_column(ForeignKey("opportunities.id"), index=True)
    document_type: Mapped[str | None] = mapped_column(String(120))
    file_url: Mapped[str | None] = mapped_column(Text)
    local_path: Mapped[str | None] = mapped_column(Text)
    extracted_text: Mapped[str | None] = mapped_column(Text)

    opportunity: Mapped[Opportunity] = relationship(back_populates="documents")


class Match(Base):
    __tablename__ = "matches"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    opportunity_id: Mapped[str] = mapped_column(ForeignKey("opportunities.id"), index=True)
    keyword: Mapped[str] = mapped_column(String(120))
    match_type: Mapped[str] = mapped_column(String(60))
    context: Mapped[str | None] = mapped_column(Text)

    opportunity: Mapped[Opportunity] = relationship(back_populates="matches")


class Evaluation(Base):
    __tablename__ = "evaluations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    opportunity_id: Mapped[str] = mapped_column(ForeignKey("opportunities.id"), index=True)
    technical_fit: Mapped[int | None] = mapped_column(default=0)
    financial_fit: Mapped[int | None] = mapped_column(default=0)
    deadline_risk: Mapped[int | None] = mapped_column(default=0)
    final_score: Mapped[int] = mapped_column(default=0)
    recommendation: Mapped[str | None] = mapped_column(String(120))

    opportunity: Mapped[Opportunity] = relationship(back_populates="evaluations")


class Alert(Base):
    __tablename__ = "alerts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    opportunity_id: Mapped[str] = mapped_column(ForeignKey("opportunities.id"), index=True)
    channel: Mapped[str] = mapped_column(String(60), default="Telegram")
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    message: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(40), default="pendiente")

    opportunity: Mapped[Opportunity] = relationship(back_populates="alerts")
