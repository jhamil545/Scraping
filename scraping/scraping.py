import requests
from bs4 import BeautifulSoup
import mysql.connector
import os
from datetime import datetime
from urllib.parse import urljoin

# Configuración de la base de datos
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': 'newspaper'
}

# Conectar a la base de datos
db_connection = mysql.connector.connect(**db_config)
cursor = db_connection.cursor()

# Crear la carpeta para almacenar imágenes si no existe
if not os.path.exists('images'):
    os.makedirs('images')

# Función para convertir la fecha al formato deseado
def convert_date(date_str):
    try:
        return datetime.strptime(date_str, '%d de %B de %Y').strftime('%Y-%m-%d')
    except ValueError:
        print(f"Formato de fecha no válido: {date_str}")
        return None

# Función para descargar la imagen
def download_image(image_url, path):
    try:
        response = requests.get(image_url)
        if response.status_code == 200:
            with open(path, 'wb') as f:
                f.write(response.content)
    except Exception as e:
        print(f"Error al descargar la imagen: {e}")

# Función para extraer y almacenar datos
def extract_and_store_data(url):
    print(f"Extrayendo datos de: {url}")
    response = requests.get(url)
    if response.status_code != 200:
        print(f"Error en la solicitud: {response.status_code}")
        return
    
    soup = BeautifulSoup(response.text, 'html.parser')
    print("Contenido HTML analizado correctamente.")
    
    # Imprimir una parte del HTML para depuración
    print(soup.prettify()[:5000])  # Imprime los primeros 5000 caracteres del HTML
    
    # Ajustar los selectores según la estructura HTML del sitio web
    title_elements = soup.select('title')  # Ajusta según la estructura real del sitio web
    date_elements = soup.select('datetime')  # Ajusta según la estructura real del sitio web
    description_elements = soup.select('tdb-block-inner')  # Ajusta según la estructura real del sitio web
    category_elements = soup.select('.td-post-category')  # Selector actualizado para categorías
    
    print(f"Se encontraron {len(title_elements)} títulos.")
    print(f"Se encontraron {len(date_elements)} fechas.")
    print(f"Se encontraron {len(description_elements)} descripciones.")
    print(f"Se encontraron {len(category_elements)} categorías.")
    
    for title_elem, date_elem, desc_elem, cat_elem in zip(title_elements, date_elements, description_elements, category_elements):
        title = title_elem.get_text(strip=True)
        date = date_elem.get_text(strip=True)
        formatted_date = convert_date(date)
        if formatted_date is None:
            continue
        
        description = desc_elem.get_text(strip=True) if desc_elem else 'No description'
        category = cat_elem.get_text(strip=True) if cat_elem else 'No category'
        
        image_url = title_elem.find('img')['src'] if title_elem.find('img') else None
        
        print(f"Title: {title}")
        print(f"Date: {date}")
        print(f"Formatted Date: {formatted_date}")
        print(f"Image URL: {image_url}")
        print(f"Description: {description}")
        print(f"Category: {category}")
        print("------------------------")
        
        if image_url:
            image_filename = title.replace(' ', '_').replace(':', '').replace('/', '_') + '.jpg'
            image_path = os.path.join('images', image_filename)
            try:
                download_image(image_url, image_path)
            except Exception as e:
                print(f"Error al descargar la imagen: {e}")

        try:
            cursor.execute(
                "INSERT INTO articles (title, url, date_published, image_url, category, description, website_id) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                (title, url, formatted_date, image_url, category, description, 1)
            )
            db_connection.commit()
            print("Datos insertados correctamente.")
        except mysql.connector.Error as err:
            print(f"Error al insertar en la base de datos: {err}")

# URL del sitio web
website_url = 'https://losandes.com.pe/'

# Llamar a la función para extraer y almacenar datos
extract_and_store_data(website_url)

# Cerrar la conexión a la base de datos
cursor.close()
db_connection.close()
