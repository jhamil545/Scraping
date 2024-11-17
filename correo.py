import requests
from bs4 import BeautifulSoup
import mysql.connector
from datetime import datetime
import re

# Configuración de la base de datos
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': 'newspaper'
}

def get_db_connection():
    return mysql.connector.connect(**db_config)

def insert_article(title, url, date_published, image_url, category, description):
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Convierte la fecha a formato DATETIME
        formatted_date = format_date(date_published)

        # Verifica si el artículo ya existe en la base de datos
        check_query = "SELECT COUNT(*) FROM articles WHERE url = %s"
        cursor.execute(check_query, (url,))
        exists = cursor.fetchone()[0]

        if not exists:
            # Inserta los datos del artículo en la tabla articles
            query = """
            INSERT INTO articles (title, url, date_published, image_url, website_id, description, category)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(query, (title, url, formatted_date, image_url, 6, description, category))
            conn.commit()

    except mysql.connector.Error as err:
        print(f"Error al insertar el artículo: {err}")
    finally:
        cursor.close()
        conn.close()

def format_date(date_str):
    # Cambiar el formato para manejar la fecha completa con hora y zona horaria
    try:
        return datetime.strptime(date_str, '%Y-%m-%dT%H:%M:%S%z')
    except ValueError as e:
        print(f"Error al formatear la fecha: {e}")
        return None  # Manejo de errores

def article_exists_in_db(url):
    """Verifica si un artículo ya existe en la base de datos mediante la URL"""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Verifica si el artículo ya existe en la base de datos por la URL
    check_query = "SELECT COUNT(*) FROM articles WHERE url = %s"
    cursor.execute(check_query, (url,))
    exists = cursor.fetchone()[0]

    cursor.close()
    conn.close()

    return exists > 0  # Retorna True si el artículo ya existe

def scrape_categories(base_url):
    response = requests.get(base_url)
    if response.status_code != 200:
        print(f"Failed to retrieve the page: {base_url}")
        return []

    soup = BeautifulSoup(response.content, 'html.parser')

    # Encuentra todas las categorías disponibles en el sitio
    category_links = []
    category_container = soup.find('ul', class_='header__featured')  # Ajusta el selector según el HTML proporcionado
    if category_container:
        for a_tag in category_container.find_all('a', href=True):
            if a_tag['href'].startswith('/'):  # Asegúrate de que el enlace sea relativo
                category_links.append(f"{base_url}{a_tag['href']}")

    return category_links

def scrape_articles_from_category(category_url, category_name):
    response = requests.get(category_url)
    if response.status_code != 200:
        print(f"Failed to retrieve the page: {category_url}")
        return

    soup = BeautifulSoup(response.content, 'html.parser')

    # Encuentra todas las URL de noticias en la categoría
    article_links = []
    for a_tag in soup.find_all('a', href=True):
        if '/edicion/' in a_tag['href'] and a_tag['href'] != category_url:  # Evitar enlaces de categoría
            article_links.append(a_tag['href'])

    # Extrae detalles de cada noticia
    for link in set(article_links):  # Usa set para evitar enlaces duplicados
        full_url = f"https://diariocorreo.pe{link}" if not link.startswith('http') else link

        # Verifica si el artículo ya está en la base de datos antes de descargar la página
        if not article_exists_in_db(full_url):
            scrape_article(full_url, category_name)  # Pasar el nombre de la categoría a la función
        else:
            print(f"El artículo ya existe en la base de datos: {full_url}")

def scrape_article(url, category_name):
    response = requests.get(url)
    if response.status_code != 200:
        print(f"Failed to retrieve the page: {url}")
        return

    soup = BeautifulSoup(response.content, 'html.parser')

    # Extraer título
    title_tag = soup.find('h1', itemprop='name')
    title = title_tag.get_text(strip=True) if title_tag else 'No title found'

    # Extraer fecha
    time_tag = soup.find('time')
    date = time_tag.get('datetime') if time_tag else 'No date found'

    # Extraer contenido
    content_div = soup.find('div', {'id': 'contenedor'})
    paragraphs = content_div.find_all('p', itemprop='description') if content_div else []
    content = ' '.join(p.get_text(strip=True) for p in paragraphs)

    # Extraer imagen
    img_tag = soup.find('img', class_='s-multimedia__image')
    img_url = img_tag.get('data-src', img_tag.get('src', 'No image found')) if img_tag else 'No image found'

    # Validación adicional para asegurarse de que el artículo pertenece a la categoría correcta
    if category_name in soup.text.upper():  # Asegura que la categoría aparezca en el contenido de la página
        # Almacenar en la base de datos
        if content:  # Solo almacenar si hay contenido
            insert_article(title, url, date, img_url, category_name, content)  # Almacena el artículo
    else:
        print(f"El artículo en {url} no pertenece a la categoría {category_name}. Se omitirá.")

# Al final de correo.py
def main():
    # URL base del sitio
    base_url = 'https://diariocorreo.pe'
    # Obtener las categorías
    category_links = scrape_categories(base_url)
    if category_links:
        for category in category_links:
            category_name = category.split('/')[-2].upper()
            print(f"Scraping category: {category_name}")
            scrape_articles_from_category(category, category_name)
        print("Extracción y almacenamiento completado.")
    else:
        print("No se encontraron categorías.")
