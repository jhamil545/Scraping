import requests
from bs4 import BeautifulSoup
import mysql.connector
from datetime import datetime, timedelta
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

def insert_website(name, url):
    conn = get_db_connection()
    cursor = conn.cursor()

    # Verifica si la URL ya existe en la tabla websites
    check_query = "SELECT COUNT(*) FROM websites WHERE url = %s"
    cursor.execute(check_query, (url,))
    exists = cursor.fetchone()[0]

    if not exists:
        # Inserta el nombre y URL del sitio web en la tabla websites
        insert_query = "INSERT INTO websites (name, url) VALUES (%s, %s)"
        cursor.execute(insert_query, (name, url))
        conn.commit()

    cursor.close()
    conn.close()

def insert_article(title, url, date_published, image_url, category, description):
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Convierte la fecha relativa a formato DATETIME
        parsed_date = parse_relative_date(date_published)
        formatted_date = format_date(parsed_date)

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
            cursor.execute(query, (title, url, formatted_date, image_url, '2', description, category))
            conn.commit()

    except mysql.connector.Error as err:
        print(f"Error al insertar el artículo: {err}")
    finally:
        cursor.close()
        conn.close()

def scrape_news_page(news_url):
    response = requests.get(news_url)
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Encuentra la categoría
        category_container = soup.find('div', class_='post-cats-bd')
        if category_container:
            category_elements = category_container.find_all('a')
            categories = [category.text.strip() for category in category_elements]
            categories = ', '.join(categories) if categories else 'No category'
        else:
            categories = 'No category'
        
        # Encuentra el elemento <img> con la imagen
        image_element = soup.find('img', class_='wp-post-image')
        image_url = image_element.get('src') if image_element else None
        
        # Encuentra la descripción del artículo
        paragraphs = soup.find_all('p')
        description = ' '.join(p.text.strip() for p in paragraphs)
        
        return image_url, categories, description
    else:
        print(f"Error al acceder a la noticia: {news_url}")
        return None, 'Error al cargar la página', 'No description'

def parse_relative_date(relative_date_str):
    now = datetime.now()
    days_match = re.search(r'(\d+)\s*días?\s*atrás', relative_date_str)
    hours_match = re.search(r'(\d+)\s*horas?\s*atrás', relative_date_str)
    minutes_match = re.search(r'(\d+)\s*mins?\s*atrás', relative_date_str)
    
    if days_match:
        days = int(days_match.group(1))
        return now - timedelta(days=days)
    elif hours_match:
        hours = int(hours_match.group(1))
        return now - timedelta(hours=hours)
    elif minutes_match:
        minutes = int(minutes_match.group(1))
        return now - timedelta(minutes=minutes)
    else:
        # Maneja el caso en el que la fecha no esté en el formato esperado
        print(f"Fecha no reconocida: {relative_date_str}")
        return now  # Fallback to current time if the format is not recognized

def format_date(date_obj):
    return date_obj.strftime('%Y-%m-%d %H:%M:%S')

def scrape_category_page(category_url):
    response = requests.get(category_url)
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Encuentra los títulos y URLs de las noticias
        title_elements = soup.find_all('h3', class_='entry-title')
        date_elements = soup.find_all('div', class_='post-date-bd')
        
        for title_element, date_element in zip(title_elements, date_elements):
            title = title_element.a.text.strip()
            date = date_element.text.strip()
            news_url = title_element.a['href'].strip()

            # Extrae la categoría, la URL de la imagen y la descripción del artículo
            image_url, categories, description = scrape_news_page(news_url)

            # Inserta los datos del artículo en la base de datos
            insert_article(title, news_url, date, image_url, categories, description)

            print(f"\nTítulo: {title}")
            print(f"Fecha: {date}")
            print(f"Categoría(s): {categories}")
            print(f"URL: {news_url}")
            print(f"URL de la imagen: {image_url if image_url else 'No image URL'}")
            print(f"Descripción: {description if description else 'No description'}")
            print("-" * 40)

    else:
        print(f"Error al realizar el scraping en la categoría: {response.status_code}")

def main():
    base_url = 'https://diariosinfronteras.com.pe'
    categories = [
        'arequipa', 'moquegua', 'puno', 'tacna', 'deportes', 'economia', 'mundo',
        'nacional', 'policiales', 'politica'
    ]

    # Inserta el nombre y URL del sitio web en la tabla websites si aún no está insertado
    insert_website('Diario Sin Fronteras', base_url)

    for category in categories:
        category_url = f'{base_url}/category/{category}/'
        print(f"Scraping category: {category_url}")
        scrape_category_page(category_url)

    print("Extracción y almacenamiento exitoso")

if __name__ == "__main__":
    main()
