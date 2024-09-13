import requests
from bs4 import BeautifulSoup

def scrape_articles_from_category(category_url):
    response = requests.get(category_url)
    if response.status_code != 200:
        print(f"Failed to retrieve the page: {category_url}")
        return

    soup = BeautifulSoup(response.content, 'html.parser')

    # Encuentra todas las URL de noticias en la categoría
    article_links = []
    for a_tag in soup.find_all('a', href=True):
        if '/politica/' in a_tag['href'] or '/deportes/' in a_tag['href']:  # Ajusta según la categoría
            article_links.append(a_tag['href'])

    # Extrae detalles de cada noticia
    for link in set(article_links):  # Usa set para evitar enlaces duplicados
        full_url = f"https://diariocorreo.pe{link}" if not link.startswith('http') else link
        scrape_article(full_url)

def scrape_article(url):
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
    img_tag = soup.find('img')  # Usa un selector más genérico para encontrar imágenes
    img_url = img_tag['src'] if img_tag and img_tag.has_attr('src') else 'No image found'

    # Imprimir resultados
    print(f"Title: {title}")
    print(f"Date: {date}")
    print(f"Image URL: {img_url}")
    print(f"Content: {content}")
    print("="*50)  # Separator between articles

# URL de la categoría
category_url = 'https://diariocorreo.pe/politica/'  # Ajusta la URL según la categoría que te interese
scrape_articles_from_category(category_url)