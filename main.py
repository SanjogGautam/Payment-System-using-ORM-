from sqlalchemy import create_engine, Column, Integer, String, ForeignKey
from sqlalchemy.orm import DeclarativeBase,sessionmaker,relationship,Mapped,mapped_column
db_url="sqlite:///mydatabase.db"
engine=create_engine(db_url)
sessions=sessionmaker(bind=engine)
Session=sessions()
class base(DeclarativeBase):
    pass
class User(base):
    __tablename__='users'
    id:Mapped[int]=mapped_column(primary_key=True)
    name:Mapped[str]=mapped_column()
    email:Mapped[str]=mapped_column(unique=True)
class Vendor(base):
    __tablename__="vendors"
    id:Mapped[int]=mapped_column(primary_key=True)
class Product(base):
    pass