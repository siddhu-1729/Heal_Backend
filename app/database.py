import os 
from dotenv import load_dotenv
from sqlalchemy import URL, create_engine
from sqlalchemy.orm import sessionmaker, declarative_base


# engine = create_engine(
#     DATABASE_URL, connect_args={"check_same_thread": False}
# )

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL,
    pool_pre_ping=True,        # 🔥 REQUIRED
    pool_recycle=300,          # 🔥 closes stale connections
    )

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)
# EVEN BETTER VERSION TO CRETATE DATABASE ENGINE
# DATABASE_URL = URL.create(
#     drivername="postgresql+psycopg2",
#     username=os.getenv("DATABASE_USER"),
#     password=os.getenv("DATABASE_PASSWORD"),
#     host=os.getenv("DATABASE_HOST"),
#     port=os.getenv("DATABASE_PORT"),
#     database=os.getenv("DATABASE_NAME"),
# )

engine=create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()
