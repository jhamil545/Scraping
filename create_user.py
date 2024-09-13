from app import db, User, app  # Asegúrate de que 'app' y 'db' están correctamente importados
from werkzeug.security import generate_password_hash
from datetime import datetime

def create_user():
    # Verifica si ya hay usuarios en la base de datos
    if not db.session.query(User).first():
        hashed_password = generate_password_hash('12345678', method='pbkdf2:sha256')
        new_user = User(
            username='nuevo_usuario',  # Agrega un nombre de usuario
            email='apazaj771@gmail.com',
            password=hashed_password,
            first_name='Nombre',  # Opcional
            last_name='Apellido',  # Opcional
            role='admin'  # Opcional, asigna un rol si es necesario
        )
        db.session.add(new_user)
        db.session.commit()
        print("Usuario creado exitosamente.")
    else:
        print("Ya existe un usuario en la base de datos.")

if __name__ == '__main__':
    with app.app_context():  # Usa el contexto de la app para trabajar con la base de datos
        db.create_all()      # Crea la tabla 'users' si no existe
        create_user()        # Crea un usuario con los datos de email y password
