from sqlalchemy import Column, String, Integer, DateTime, Text, ForeignKey, func
from sqlalchemy.orm import relationship
from database.connection import Base

class Repair(Base):
    __tablename__ = "repairs"

    id = Column(String(50), primary_key=True)
    asset_id = Column(String(50), ForeignKey("assets.id", ondelete="CASCADE"), nullable=True)
    reported_by = Column(String(50), ForeignKey("employees.id", ondelete="CASCADE"), nullable=False)
    issue = Column(String(150), nullable=False)
    description = Column(Text)
    request_date = Column(String(50), nullable=False)
    priority = Column(String(20), nullable=False)  # Low, Medium, High
    assigned_to = Column(String(100), default="IT Support Team")
    estimated_completion = Column(String(100), default="Awaiting inspection")
    status = Column(String(20), nullable=False, default="Pending")  # Pending, In Progress, Awaiting Parts, Completed, Cancelled
    accepted_by = Column(String(100))
    accepted_date = Column(String(50))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationship to updates
    updates = relationship("RepairUpdate", back_populates="repair", cascade="all, delete-orphan", order_by="RepairUpdate.id")

class RepairUpdate(Base):
    __tablename__ = "repair_updates"

    id = Column(Integer, primary_key=True, autoincrement=True)
    repair_id = Column(String(50), ForeignKey("repairs.id", ondelete="CASCADE"), nullable=False)
    date = Column(String(50), nullable=False)
    message = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    repair = relationship("Repair", back_populates="updates")
