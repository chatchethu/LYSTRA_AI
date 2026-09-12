from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import String, Float
from sqlalchemy.dialects.postgresql import JSONB
from .base import Base

class MetricEvent(Base):
    __tablename__ = 'metric_events'
    
    metric_type: Mapped[str] = mapped_column(String, index=True)
    value: Mapped[float] = mapped_column(Float, default=1.0)
    attributes: Mapped[dict] = mapped_column(JSONB, default=dict)
