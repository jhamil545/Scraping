from flask import Blueprint, redirect, url_for, session, render_template, request, flash, Response
import csv
from datetime import datetime, timedelta
from sqlalchemy import text
import io
import json
from models import db, Article,User, Website
from mako.template import Template
from mako.lookup import TemplateLookup

from wordcloud import WordCloud
from io import BytesIO
import base64
# Configuración de Blueprint y Mako
dashboard = Blueprint('dashboard', __name__, template_folder='dist', static_folder='static')

# Configura Mako para buscar plantillas en el directorio 'dist'
lookup = TemplateLookup(directories=['dist'])

# Función para obtener la URL de archivos estáticos
def static_url(filename):
    return url_for('static', filename=filename)



@dashboard.route('/dashboard')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    # Fecha actual y hace 15 días
    today = datetime.today().date()
    fifteen_days_ago = today - timedelta(days=15)

    # Contar artículos del día actual
    articles_today_count = db.session.query(Article).filter(Article.date_published >= today).count()
    total_articles_count = db.session.query(Article).count()

    # Definir las fechas de inicio y fin para los últimos 15 días
    today = datetime.now()
    fifteen_days_ago = today - timedelta(days=14)

    # Obtener el número de artículos por día en los últimos 15 días
    query = text("""
        SELECT DATE(date_published) AS date, COUNT(*) AS count
        FROM articles
        WHERE DATE(date_published) >= :start_date
        GROUP BY DATE(date_published)
        ORDER BY DATE(date_published) DESC
        LIMIT 15
    """)
    results = db.session.execute(query, {'start_date': fifteen_days_ago})

    # Procesar los resultados de la consulta
    counts_dict = {row.date.strftime('%Y-%m-%d'): row.count for row in results}

    # Crear lista de los últimos 15 días y conteo de artículos
    all_dates = [(today - timedelta(days=i)).strftime('%Y-%m-%d') for i in range(15)]
    all_counts = [counts_dict.get(date, 0) for date in all_dates]
    dates_and_counts = [{'date': date, 'count': count} for date, count in zip(all_dates, all_counts)]
    
    # Convertir `dates_and_counts` a JSON
    dates_and_counts_json = json.dumps(dates_and_counts)

    # Consulta para obtener el número de artículos por categoría
    category_query = text("""
        SELECT category, COUNT(*) AS article_count
        FROM (
            SELECT TRIM(SUBSTRING_INDEX(SUBSTRING_INDEX(category, ',', numbers.n), ',', -1)) AS category
            FROM articles
            JOIN (
                SELECT 1 n UNION ALL SELECT 2 UNION ALL SELECT 3 UNION ALL SELECT 4 UNION ALL SELECT 5
                UNION ALL SELECT 6 UNION ALL SELECT 7 UNION ALL SELECT 8 UNION ALL SELECT 9 UNION ALL SELECT 10
            ) numbers ON CHAR_LENGTH(category) - CHAR_LENGTH(REPLACE(category, ',', '')) >= numbers.n - 1
        ) AS subquery
        GROUP BY category
        ORDER BY category
    """)
    category_results = db.session.execute(category_query)
    categories_and_counts = [{'category': row.category, 'count': row.article_count} for row in category_results]

    # Consulta para obtener el nombre del sitio web y la cantidad de artículos
    website_counts_query = text("""
        SELECT w.name AS website_name, COUNT(a.id) AS article_count
        FROM websites w
        JOIN articles a ON a.website_id = w.id
        GROUP BY w.name
        ORDER BY w.name
    """)
    website_counts_result = db.session.execute(website_counts_query)
    website_counts = list(website_counts_result)

    # Crear listas de datos de sitios web y conteo de artículos
    websites = [row.website_name for row in website_counts]
    website_article_counts = [row.article_count for row in website_counts]

    # Convertir listas de sitios web y conteos a JSON
    websites_json = json.dumps(websites)
    website_article_counts_json = json.dumps(website_article_counts)

    # Consulta SQL para obtener el número de artículos por mes por sitio web en el año actual
    monthly_articles_query = text("""
        SELECT 
            w.name AS website_name,
            MONTH(a.date_published) AS month,
            COUNT(a.id) AS article_count
        FROM articles a
        JOIN websites w ON a.website_id = w.id
        WHERE YEAR(a.date_published) = YEAR(CURDATE())  -- Solo datos del año actual
        GROUP BY w.name, MONTH(a.date_published)
        ORDER BY w.name, month;
    """)
    monthly_articles_result = db.session.execute(monthly_articles_query)

    # Procesar resultados para el gráfico de radar
    websites_data = {}
    for row in monthly_articles_result:
        website = row.website_name
        month = row.month
        count = row.article_count

        if website not in websites_data:
            websites_data[website] = [0] * 12  # Inicializar con 12 meses en 0
        websites_data[website][month - 1] = count  # Asignar el conteo al mes correspondiente

    # Preparar datasets para Chart.js
    radar_datasets = []
    colors = [
        'rgba(248, 37, 37, 0.8)', 'rgba(69,200,248,0.8)', 'rgba(99,201,122,0.8)',
        'rgba(203,82,82,0.8)', 'rgba(229,224,88,0.8)', 'rgba(148,112,202,0.8)',
    ]

    for idx, (website, data) in enumerate(websites_data.items()):
        dataset = {
            'label': website,
            'data': data,
            'borderColor': colors[idx % len(colors)],
            'backgroundColor': colors[idx % len(colors)].replace('0.8', '0.3')
        }
        radar_datasets.append(dataset)

    # Convertir los datos a JSON
    labels = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']
    labels_json = json.dumps(labels)
    radar_datasets_json = json.dumps(radar_datasets)

    # Convertimos `all_dates` y `all_counts` a JSON antes de enviarlos al template
    all_dates_str = ",".join(all_dates)
    all_counts_str = ",".join(map(str, all_counts))

    # Preparar datos de categorías
    categories = [item['category'] for item in categories_and_counts]
    counts = [item['count'] for item in categories_and_counts]

    # Consulta SQL para obtener todos los títulos de los artículos
    titles_query = db.session.query(Article.title).all()

    # Combina todos los títulos en un solo string
    text2 = " ".join([title[0] for title in titles_query])

    # Genera la nube de palabras
    wordcloud = WordCloud(width=800, height=400, background_color="white").generate(text2)

    # Guarda la nube de palabras en una imagen en memoria
    img = BytesIO()
    wordcloud.to_image().save(img, format="PNG")
    img.seek(0)
    img_base64 = base64.b64encode(img.getvalue()).decode('utf-8')

    
    

    # Renderiza la plantilla
    template = lookup.get_template('index-d.html')
    return template.render(
        articles_today_count=articles_today_count, 
        total_articles_count=total_articles_count, 
        dates_and_counts=dates_and_counts,
        categories=categories,
        counts=counts,
        websites=websites, 
        website_article_counts=website_article_counts,
        all_dates_str=all_dates_str,  
        all_counts_str=all_counts_str,  
        websites_json=websites_json,       
        website_article_counts_json=website_article_counts_json,
        labels_json=labels_json, radar_datasets_json=radar_datasets_json,
        img_base64=img_base64,
        static_url=static_url, 
        url_for=url_for
    )
@dashboard.route('/dashboard2')
def dashboard2():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    template = lookup.get_template('index-1.html')
    return template.render()

@dashboard.route('/articles')
def list_articles():
    # Consultar artículos junto con el nombre del sitio web y devolver instancias de Article
    articles = db.session.query(
        Article,
        Website.name.label('website_name')  # Alias para el nombre del sitio web
    ).join(
        Website, Article.website_id == Website.id
    ).order_by(
        Article.date_published.desc()
    ).all()

    # Convertir los resultados a un formato fácilmente accesible
    formatted_articles = [
        {
            'id': article.id, 
            'title': article.title,
            'url': article.url,
            'date_published': article.date_published,
            'image_url': article.image_url,
            'description': article.description,
            'category': article.category,
            'website_name': website_name
        }
        for article, website_name in articles
    ]

    return render_template('listarticles.html', articles=formatted_articles)



@dashboard.route('/user')
def list_user():
    users = db.session.query(User).all()  # Esto devuelve objetos Article completos
    return render_template('listaruser.html   ', users=users)  # Cambia a .mako si usas Mako

@dashboard.route('/export_csv', methods=['GET'])
def export_csv():
    # Obtener los filtros de la URL
    title = request.args.get('title', None)
    date = request.args.get('date', None)
    category = request.args.get('category', None)

    # Obtener los artículos filtrados
    articles = get_filtered_articles(title=title, date=date, category=category)

    # Validar que se hayan encontrado artículos
    if not articles:
        flash('No se encontraron artículos con los filtros aplicados.')
        return redirect(url_for('dashboard.index'))

    # Crear un objeto StringIO para almacenar los datos CSV
    output = io.StringIO()
    writer = csv.writer(output)

    # Escribir encabezados
    writer.writerow(['Title', 'URL', 'Date Published', 'Image', 'Website', 'Description', 'Category'])

    # Escribir los datos de los artículos
    for article in articles:
        writer.writerow([article.title, article.url, article.date_published.strftime('%Y-%m-%d'),
                         article.image_url, article.website_id, article.description, article.category])

    # Configurar la respuesta HTTP para descargar el archivo CSV
    output.seek(0)
    return Response(output, mimetype='text/csv', headers={"Content-Disposition": "attachment;filename=articles.csv"})

def get_filtered_articles(title=None, date=None, category=None):
    query = db.session.query(Article)

    if title:
        query = query.filter(Article.title.ilike(f'%{title}%'))
    if date:
        query = query.filter(Article.date_published == date)
    if category:
        query = query.filter(Article.category.ilike(f'%{category}%'))

    return query.all()
