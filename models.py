from sqlalchemy import Column, Integer, String, ForeignKey, DECIMAL
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

from database import engine

Base = declarative_base()

class LottoStore(Base):
    __tablename__ = "lotto_stores"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    address = Column(String(255), nullable=False)
    phone = Column(String(30))
    lat = Column(DECIMAL(10, 8))
    lon = Column(DECIMAL(11, 8))
    first_prize = Column(Integer, default=0)
    second_prize = Column(Integer, default=0)
    score = Column(Integer, default=0)
    
    winning_infos = relationship("WinningInfo", back_populates="store")
    
    @classmethod
    def delete_all(cls, session):
        session.query(cls).delete()
        session.commit()

class WinningInfo(Base):
    __tablename__ = "winning_infos"
    
    id = Column(Integer, primary_key=True, index=True)
    store_id = Column(Integer, ForeignKey("lotto_stores.id"), nullable=False)
    draw_no = Column(Integer, nullable=False)
    rank = Column(Integer, nullable=False)
    category = Column(String(10))
    
    store = relationship("LottoStore", back_populates="winning_infos")
    
    @classmethod
    def get_latest_drwNo(cls, session):
        latest_winning_info = session.query(cls).order_by(cls.draw_no.desc()).first()
        if latest_winning_info:
            return latest_winning_info.draw_no
        return None