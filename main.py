from flask import Flask, render_template, request, redirect, url_for, session, make_response
import db
from models import Productos, Clientes, Imagenes, Pedidos  # Importamos los modelos necesarios
import base64

app = Flask(__name__)  # Creamos la aplicación Flask
app.secret_key = 'claveprueba'  # Clave secreta para sesiones

# Ruta principal, renderiza la página de inicio
@app.route("/")
def home():
    session.pop('current_page', None)  # Limpiamos 'current_page' de la sesión si existe
    return render_template('index.html')

# Ruta para validar el inicio de sesión
@app.route('/crear', methods=["POST"])
def validacion():
    nombre = request.form.get('nombre')
    contraseña = request.form.get('contraseña')

    # Verifica si es el administrador
    if nombre == 'admin' and contraseña == "1234":
        session['admin'] = True
        return redirect(url_for('acceder'))
    else:
        # Verifica si es un cliente registrado
        session['nombre'] = nombre
        resultado = db.session.query(Clientes).all()
        for fila in resultado:
            if fila.nombre.lower() == nombre.lower() and fila.password == contraseña:
                session['admin'] = False
                return redirect(url_for('acceder'))
        else:
            # Si no se encuentra la identificación, muestra un error
            return render_template("index.html", error="Identificación no encontrada. Por favor, inténtalo de nuevo.")

# Ruta principal después del inicio de sesión, muestra los productos disponibles
@app.route('/acceder', methods=["POST", "GET"])
def acceder(identificacion=[]):

    productos_con_imagenes = []

    # Si se pasa una lista de productos (resultado de una búsqueda), mostrar esos productos
    if identificacion:
        for producto in identificacion:
            imagenes = db.session.query(Imagenes).filter_by(id=producto.id).one()
            encoded_image = base64.b64encode(imagenes.image_data).decode('utf-8') if imagenes.image_data else None
            productos_con_imagenes.append({
                'id': producto.id,
                'nombre': producto.nombre,
                'precio': producto.precio,
                'descripcion': producto.descripcion,
                'imagen': encoded_image,
                'stock': True if int(producto.stock) > 0 else False
            })
        return render_template("web.html", productos=productos_con_imagenes,admin=session['admin'])

    # Configuración de paginación
    page = request.args.get('page', '1')

    if 'current_page' not in session:
        session['current_page'] = 1

    if page == 'Prev':
        session['current_page'] = max(session['current_page'] - 1, 1)
    elif page == 'Next':
        session['current_page'] += 1
    else:
        try:
            session['current_page'] = int(page)
        except ValueError:
            session['current_page'] = 1

    current_page = session['current_page']

    offset = (current_page - 1) * 12  # Calcula el offset para la paginación
    # Consulta productos e imágenes para mostrar en la página actual
    imagenes_guardadas = db.session.query(Imagenes).offset(offset).limit(12).all()
    productos = db.session.query(Productos).offset(offset).limit(12).all()

    # Preparar datos de productos con imágenes codificadas en base64
    productos_con_imagenes = []
    if productos:
        for producto, imagen in zip(productos, imagenes_guardadas):
            encoded_image = base64.b64encode(imagen.image_data).decode(
                'utf-8') if imagen and imagen.image_data else None
            productos_con_imagenes.append({
                'id': producto.id,
                'nombre': producto.nombre,
                'precio': producto.precio,
                'descripcion': producto.descripcion,
                'imagen': encoded_image,
                'stock': True if int(producto.stock) > 0 else False
            })

    total_productos = db.session.query(Productos).count()  # Total de productos en la base de datos
    has_prev = current_page > 1  # Indica si hay productos anteriores para la página anterior
    carrito = []
    total = 0
    if session["admin"] == False:
        nombre = session['nombre']
        ids = session[f'{nombre}']['productos_carrito']  # Obtiene los productos en el carrito del usuario
        if ids:
            for id_producto in ids:
                producto = db.session.query(Productos).filter_by(id=id_producto).first()
                imagen = db.session.query(Imagenes).filter_by(id=id_producto).first()
                if producto and imagen:
                    total += producto.precio
                    carrito.append({
                        'id': producto.id,
                        'nombre': producto.nombre,
                        'precio': producto.precio,
                        'imagen': base64.b64encode(imagen.image_data).decode('utf-8') if imagen and imagen.image_data else None
                    })

    # Renderiza la plantilla con los productos, carrito y paginación
        return render_template("web.html", productos=productos_con_imagenes, carrito=carrito, total=total,
                            page=current_page, has_prev=has_prev,admin=session['admin'])
    else:
        return render_template("web.html", productos=productos_con_imagenes, total=total,
                               page=current_page, has_prev=has_prev, admin=session['admin'])

# Ruta para registrarse
@app.route('/signup')
def registrar():
    return render_template("register.html")

# Ruta para agregar un nuevo registro de cliente
@app.route('/signup-f', methods=["POST"])
def agg_registro():
    nombre = request.form.get('nombre')
    edad = request.form.get('edad')
    contraseña = request.form.get('contraseña')
    repetir_contraseña = request.form.get('repetir_contraseña')

    # Validación de campos del formulario de registro
    if contraseña != repetir_contraseña:
        return render_template("register.html", error="Las contraseñas no coinciden. Por favor, inténtalo de nuevo.")
    elif not contraseña or not repetir_contraseña or not edad or not nombre:
        return render_template("register.html", error="Los campos no pueden estar incompletos. Por favor, inténtalo de nuevo.")
    elif len(contraseña) < 4:
        return render_template("register.html", error='La contraseña debe tener al menos 4 caracteres')
    else:
        # Crear un nuevo registro de cliente en la base de datos
        persona = Clientes(nombre=nombre, edad=edad, password=contraseña)
        db.session.add(persona)
        db.session.commit()
        session['pedido'] = False
        session[f'{nombre}'] = {'id': persona.id, 'productos_carrito': []}  # Inicializar la sesión del usuario
        print(persona.id)
        return redirect(url_for('home'))  # Redirigir al inicio después del registro exitoso

# Ruta para agregar una imagen de producto
@app.route('/add-image')
def imagenes():
    return render_template("agregar_productos.html")

# Ruta para procesar la imagen del producto
@app.route('/add-image-f', methods=["POST"])
def revisar_producto():
    nombre = request.form.get('nombre')
    precio = request.form.get('precio')
    descripcion = request.form.get('descripcion')
    stock = request.form.get('stock')
    imagen = request.files['imagen']
    imagen_data = imagen.read()

    # Validaciones para los campos del formulario de agregar producto
    if len(nombre) > 150:
        return render_template('agregar_productos.html', error='Error: Máximo 100 caracteres para el nombre')
    elif not imagen:
        return render_template('agregar_productos.html', error="Error: Agrega una imagen")
    elif not nombre or not precio or not stock:
        return render_template('agregar_productos.html', error="Error: Nombre,precio y stock son obligatorios.")
    elif not precio.isnumeric():
        return render_template('agregar_productos.html', error='Error: El precio solo admite números')
    elif len(nombre) > 30:
        return render_template('agregar_productos.html', error='Error: nombre max  30 caracteres')

    mostrar_estructura = False
    if 'mostrar' in request.form:
        mostrar_estructura = True
        imagen_base64 = base64.b64encode(imagen_data).decode('utf-8')
        return render_template('agregar_productos.html', mostrar_estructura=mostrar_estructura,
                               imagen_data=imagen_base64, nombre=nombre, precio=precio, descripcion=descripcion,
                               imagen=imagen_base64, stock=stock)
    return render_template('agregar_productos.html')

# Ruta para agregar un nuevo producto a la base de datos
@app.route('/add-product', methods=["POST"])
def agregar_nuevo_producto():
    nombre = request.form.get('nombre')
    precio = request.form.get('precio')
    descripcion = request.form.get('descripcion')
    stock = request.form.get('stock')
    imagen_base64 = request.form['imagenes']
    imagen_data = base64.b64decode(imagen_base64)

    # Crear nuevo producto y su imagen asociada en la base de datos
    producto = Productos(nombre=nombre, precio=precio, stock=stock, descripcion=descripcion)
    imagen = Imagenes(image_data=imagen_data)
    db.session.add(imagen)
    db.session.add(producto)
    db.session.commit()
    return redirect(url_for('acceder'))  # Redirigir a la página principal después de agregar el producto

# Ruta para agregar productos al carrito de compras
@app.route('/enviar_datos', methods=["POST"])
def agregar_al_carrito():
    id_producto = request.form.get('producto_id')
    nombre = session['nombre']
    session[f'{nombre}']['productos_carrito'].append(id_producto)
    session.modified = True  # Marcar la sesión como modificada después de agregar el producto al carrito
    return redirect(url_for('acceder'))

# Ruta para eliminar productos del carrito de compras
@app.route('/eliminar_datos', methods=["POST"])
def eliminar_carrito():
    id_producto = request.form.get('producto_id')
    nombre = session.get('nombre')
    if nombre and nombre in session and 'productos_carrito' in session[nombre]:
        if id_producto in session[nombre]['productos_carrito']:
            session[nombre]['productos_carrito'].remove(id_producto)
            session.modified = True  # Marcar la sesión como modificada después de eliminar el producto del carrito
    return redirect(url_for('acceder'))

# Ruta para buscar productos por nombre
@app.route('/buscar_datos', methods=["GET"])
def buscar_datos():
    datos = request.args.get('datos')
    resultado = db.session.query(Productos).filter(Productos.nombre.ilike(f"%{datos}%")).all()
    return acceder(resultado)  # Redirigir a la página principal con los resultados de la búsqueda

# Ruta para mostrar el perfil del usuario
@app.route('/perfil', methods=["POST", "GET"])
def perfil():
    nombre = session['nombre']
    id = session[f'{nombre}']['id']
    datos = []
    if id:
        datos = db.session.query(Clientes).filter_by(id=id).one()
    return render_template('perfil.html', datos=datos)

# Ruta para mostrar la interfaz de administrador
@app.route('/admin', methods=["POST", "GET"])
def admin():
    return render_template('admin.html')

# Ruta para crear pedidos basados en los productos del carrito
@app.route('/pedido', methods=["GET", "POST"])
def crear_pedido():
    nombre = session['nombre']
    productos = session[f'{nombre}']['productos_carrito']
    for producto in productos:
        p1 = Pedidos(cliente_id=session[f'{nombre}']['id'], estado="EN PROCESO", cantidad=1)
        db.session.add(p1)

    session[f'{nombre}']['productos_carrito'] = []  # Limpiar carrito después de crear pedidos
    session.modified = True
    session['pedido'] = True
    db.session.commit()  # Realizar commit de las transacciones en la base de datos

    return redirect(url_for('acceder'))  # Redirigir a la página principal después de crear el pedido
@app.route('/eliminar-pedido',methods=['GET'])
def eliminar_pedido():
    id_pedido = request.args.get('id_pedido')
    pedido = db.session.query(Pedidos).filter_by(id=id_pedido).one()
    if pedido:
        db.session.delete(pedido)
        db.session.commit()
    return redirect(url_for('perfil'))

# Ruta para eliminar un cliente de la base de datos
@app.route('/eliminar-cliente', methods=["POST", "GET"])
def eliminar_cliente():
    if request.method == 'GET':
        clientes = db.session.query(Clientes).all()
        pedidos = db.session.query(Pedidos).all()
        return render_template('eliminar_cliente.html', clientes=clientes,pedidos=pedidos)

    if request.method == 'POST':
        cliente_id = request.form.get('cliente_id')
        if cliente_id:
            clientes = db.session.query(Clientes).all()
            cliente = db.session.query(Clientes).filter_by(id=cliente_id).first()
            pedidos = db.session.query(Pedidos).all()
            for pedido in pedidos:
                if pedido.cliente_id == cliente.id:
                    return render_template('eliminar_cliente.html',error="Este Cliente aun cuenta con pedidos pendientes",clientes=clientes,pedidos=pedidos)
            else:
                db.session.delete(cliente)
                db.session.commit()
        return redirect(url_for('eliminar_cliente'))

# Ruta para editar información de un cliente
@app.route('/editar-cliente', methods=['GET', 'POST'])
def editar_cliente():
    if request.method == 'POST':
        # Obtener datos del formulario para editar cliente
        cliente_id = request.form.get('cliente_id')
        nombre = request.form.get('nombre')
        edad = request.form.get('edad')
        contraseña = request.form.get('contraseña')

        # Actualizar el cliente en la base de datos
        cliente = db.session.query(Clientes).filter_by(id=cliente_id).one()
        if nombre:
            if len(nombre) > 30:
                return render_template("editar_cliente.html", error="Max 30 caracteres")
            cliente.nombre = nombre
        if edad:
            cliente.edad = int(edad)
        if contraseña:
            if len(contraseña) < 4:
                return render_template("editar_cliente.html", error="Minimo 4 digitos")
            cliente.password = contraseña
        db.session.commit()
        return redirect(url_for('editar_cliente'))
    else:
        # Mostrar todos los clientes para la edición
        clientes = db.session.query(Clientes).all()
        return render_template('editar_cliente.html', clientes=clientes)

# Ruta para eliminar un producto de la base de datos
@app.route('/eliminar-producto', methods=["POST", "GET"])
def eliminar_producto():
    if request.method == 'GET':
        productos = db.session.query(Productos).all()
        return render_template('eliminar_producto.html', productos=productos)

    if request.method == 'POST':
        producto_id = request.form.get('producto_id')
        if producto_id:
            producto = db.session.query(Productos).filter_by(id=producto_id).first()

            if producto:
                db.session.delete(producto)
                db.session.commit()

        return redirect(url_for('eliminar_producto'))

# Ruta para editar información de un producto
@app.route('/editar-producto', methods=['GET', 'POST'])
def editar_producto():
    if request.method == 'POST':
        # Obtener datos del formulario para editar producto
        producto_id = request.form.get('producto_id')
        nombre = request.form.get('nombre')
        precio = request.form.get('precio')
        stock = request.form.get('stock')

        # Actualizar el producto en la base de datos
        producto = db.session.query(Productos).filter_by(id=producto_id).one()
        if nombre and len(nombre) < 30:
            producto.nombre = nombre
        if precio:
            producto.precio = float(precio)
        if stock:
            producto.stock = int(stock)
        db.session.commit()
        return redirect(url_for('editar_producto'))
    else:
        # Mostrar todos los productos para la edición
        productos = db.session.query(Productos).all()
        return render_template('editar_producto.html', productos=productos)

# Ejecución de la aplicación Flask
if __name__ == "__main__":
    db.Base.metadata.create_all(db.engine)  # Crear nuevas tablas al iniciar la aplicación
    app.run(debug=True)  # Ejecutar la aplicación en modo debug
