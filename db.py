from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

#engine = create_engine('postgresql://postgres@host/database')
engine = create_engine("postgresql://postgres:0023@localhost:5432/productos")
#si la base de datos no existe la creamos
#creamos la session que sepa quien acceda a la base de datos parta tener un control
Session = sessionmaker(bind=engine)
session = Session()
Base = declarative_base()
 