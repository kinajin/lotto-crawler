from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker



# AWS RDS PostgreSQL 데이터베이스
SQLALCHEMY_DATABASE_URL = "postgresql://postgres:root@3.34.216.218:5432/lotto"

# 희경 로컬 PostgreSQL 데이터베이스
# LOCAL_SQLALCHEMY_DATABASE_URL = "postgresql://lotto:password@localhost:5432/lotto_db"

# Docker 컨테이너의 PostgreSQL 데이터베이스
# DOCKER_SQLALCHEMY_DATABASE_URL = "postgresql://lotto:password@localhost:5433/lotto_db"


engine = create_engine(DOCKER_SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)