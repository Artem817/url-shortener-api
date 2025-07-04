from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, func

from app.database import Base


class URL(Base):
    __tablename__ = 'urls'

    id = Column(Integer, primary_key=True, autoincrement=True)
    url = Column(String(2083), nullable=False)
    access_count = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    def __str__(self):
        created_str = self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else 'N/A'
        updated_str = self.updated_at.strftime('%Y-%m-%d %H:%M:%S') if self.updated_at else 'N/A'
        return (f"URL(ID: {self.id}, URL: {self.url}, Accesses: {self.access_count}, "
                f"Created: {created_str}, Updated: {updated_str})")
