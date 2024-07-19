import db
from sqlalchemy import Column, Integer, String, TIMESTAMP, Float, LargeBinary, ForeignKey, Table
from sqlalchemy.orm import relationship
from datetime import datetime

# Definición de la tabla de asociación para pedidos y productos
association_table = Table('pedido_producto', db.Base.metadata,
    Column('pedido_id', Integer, ForeignKey('pedidos.id')),
    Column('producto_id', Integer, ForeignKey('productos.id')),
    Column('cantidad', Integer, nullable=False),
    Column('precio_unitario', Float, nullable=False)
)

# Definición del modelo de Clientes
class Clientes(db.Base):
    __tablename__ = "clientes"
    id = Column(Integer, primary_key=True, autoincrement=True)
    nombre = Column(String(30), nullable=False)
    edad = Column(Integer, nullable=False)
    password = Column(String(100))
    fecha_de_registro = Column(TIMESTAMP, default=datetime.utcnow)

    # Relación uno a muchos con Pedidos
    pedidos = relationship("Pedidos", back_populates="cliente")

    def __init__(self, nombre, edad, password):
        self.nombre = nombre
        self.edad = edad
        self.password = password

    def __str__(self):
        return "{}: {} :{} :{} :{}".format(self.id, self.nombre, self.edad, self.password, self.fecha_de_registro)


# Definición del modelo de Productos
class Productos(db.Base):
    __tablename__ = "productos"
    id = Column(Integer, primary_key=True, autoincrement=True)
    nombre = Column(String(30), unique=True)
    precio = Column(Float)
    descripcion = Column(String(150))
    stock = Column(Integer)

    # Relación uno a muchos con Imagenes
    imagenes = relationship("Imagenes", back_populates="producto")

    # Relación muchos a muchos con Pedidos a través de la tabla de asociación
    pedidos = relationship("Pedidos", secondary=association_table, back_populates="productos")


# Definición del modelo de Imagenes
class Imagenes(db.Base):
    __tablename__ = "imagenes"
    id = Column(Integer, primary_key=True, autoincrement=True)
    producto_id = Column(Integer, ForeignKey('productos.id'))
    image_data = Column(LargeBinary)

    # Relación muchos a uno con Productos
    producto = relationship("Productos", back_populates="imagenes")


# Definición del modelo de Pedidos
class Pedidos(db.Base):
    __tablename__ = 'pedidos'
    id = Column(Integer, primary_key=True, autoincrement=True)
    cliente_id = Column(Integer, ForeignKey('clientes.id'), nullable=False)
    fecha_de_registro = Column(TIMESTAMP, default=datetime.utcnow)
    estado = Column(String(50), nullable=False)
    cantidad = Column(Integer, nullable=False, default=1)

    # Relación muchos a uno con Clientes
    cliente = relationship("Clientes", back_populates="pedidos")

    # Relación muchos a muchos con Productos a través de la tabla de asociación
    productos = relationship("Productos", secondary=association_table, back_populates="pedidos")
