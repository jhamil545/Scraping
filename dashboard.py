from flask import Blueprint, redirect, url_for, session
from datetime import datetime, timedelta
from sqlalchemy import text
from models import db, Article
from mako.template import Template
from mako.lookup import TemplateLookup

# Configuración de Blueprint y Mako
dashboard = Blueprint('dashboard', __name__, template_folder='dist')

# Configura Mako para buscar plantillas en el directorio 'dist'
lookup = TemplateLookup(directories=['dist'])

# Función para obtener la URL de archivos estáticos
def static_url(filename):
    return url_for('static', filename=filename)

@dashboard.route('/dashboard')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    today = datetime.today().date()
    fifteen_days_ago = today - timedelta(days=15)

    # Contar artículos del día actual
    articles_today_count = db.session.query(Article).filter(Article.date_published >= today).count()

    # Obtener el número de artículos por día en los últimos 15 días
    query = text("""
        SELECT DATE(date_published) AS date, COUNT(*) AS count
        FROM articles
        WHERE DATE(date_published) BETWEEN :start_date AND :end_date
        GROUP BY DATE(date_published)
        ORDER BY DATE(date_published) DESC
    """)
    results = db.session.execute(query, {'start_date': fifteen_days_ago, 'end_date': today})

    dates = [row.date.strftime('%Y-%m-%d') for row in results]
    counts = [row.count for row in results]

    # Asegurarse de que haya 15 días de datos en la lista, incluso si algunos días no tienen artículos
    all_dates = [(fifteen_days_ago + timedelta(days=i)).strftime('%Y-%m-%d') for i in range(15)]
    all_counts = [0] * 15

    counts_dict = dict(zip(dates, counts))

    for i, date in enumerate(all_dates):
        if date in counts_dict:
            all_counts[i] = counts_dict[date]

    # Obtener la cantidad de noticias por categoría
    category_query = text("""
        SELECT category, COUNT(id) AS article_count
        FROM articles
        GROUP BY category
        ORDER BY category
    """)
    category_results = db.session.execute(category_query)

    # Combina los resultados en una lista de diccionarios
    categories_and_counts = [{'category': row.category, 'count': row.article_count} for row in category_results]

    # Consulta para obtener los website_id y la cantidad de artículos
    website_counts_query = text("""
        SELECT website_id, COUNT(*) AS article_count
        FROM articles
        GROUP BY website_id
    """)
    website_counts_result = db.session.execute(website_counts_query)
    
    # Crear listas para los datos
    websites = [row.website_id for row in website_counts_result if row.website_id is not None]
    website_article_counts = [row.article_count for row in website_counts_result if row.website_id is not None]

    # Combinación de fechas y conteos para la plantilla
    dates_and_counts = [{'date': date, 'count': count} for date, count in zip(all_dates, all_counts)]

    # Renderiza con Mako
    template = lookup.get_template('index-d.html')
    return template.render(
        articles_today_count=articles_today_count, 
        dates_and_counts=dates_and_counts,
        categories_and_counts=categories_and_counts,
        websites=websites, 
        website_article_counts=website_article_counts,
        static_url=static_url  # Pasa la función estática a la plantilla
    )



@dashboard.route('/dashboard2')
def dashboard2():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    template = lookup.get_template('index-1.html')
    return template.render()
