from flask import Flask, render_template, request, redirect, url_for, flash, session
from models import db, User, Article  # Asegúrate de que estos modelos estén definidos en models.py
from config import Config
from sqlalchemy import text
from werkzeug.security import check_password_hash
import threading
import time
from scraping import main as scrape_main
from correo import main as correo_main

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    db.init_app(app)
    
    with app.app_context():
        # Importa y registra el blueprint aquí para evitar importaciones circulares
        from dashboard import dashboard
        app.register_blueprint(dashboard, url_prefix='/dashboard')

        # Rutas de la aplicación
        @app.route('/')
        def home():
            # Obtener las categorías existentes, separando las múltiples
            category_query = text("""
                SELECT DISTINCT TRIM(SUBSTRING_INDEX(SUBSTRING_INDEX(category, ',', numbers.n), ',', -1)) AS category
                FROM articles
                JOIN (
                    SELECT 1 n UNION ALL SELECT 2 UNION ALL SELECT 3 UNION ALL SELECT 4 UNION ALL SELECT 5
                    UNION ALL SELECT 6 UNION ALL SELECT 7 UNION ALL SELECT 8 UNION ALL SELECT 9 UNION ALL SELECT 10
                ) numbers ON CHAR_LENGTH(category) - CHAR_LENGTH(REPLACE(category, ',', '')) >= numbers.n - 1
            """)

            query_categories = db.session.execute(category_query)
            categories = [row.category for row in query_categories.fetchall()]

            # Consultar los artículos recientes junto con el nombre de la página web, ordenados por fecha de publicación
            query_recent_articles = db.session.execute(text('''
                SELECT a.*, w.name AS website_name
                FROM articles a
                JOIN websites w ON a.website_id = w.id
                ORDER BY a.date_published DESC
                LIMIT 5
            '''))
            recent_articles = query_recent_articles.fetchall()

            # Consultar los artículos por categoría, ordenados por fecha de publicación
            articles_by_category = {}
            for category in categories:
                query_articles = db.session.execute(text('''
                    SELECT a.*, w.name AS website_name
                    FROM articles a
                    JOIN websites w ON a.website_id = w.id
                    WHERE a.category LIKE :category
                    ORDER BY a.date_published DESC
                '''), {'category': f'%{category}%'})
                articles_by_category[category] = query_articles.fetchall()

            return render_template(
                'index.html',
                categories=categories,
                recent_articles=recent_articles,
                articles_by_category=articles_by_category
            )

        @app.route('/category')
        def category():
            # Obtener las categorías existentes y el nombre del sitio web correspondiente
            category_query = text("""
                SELECT DISTINCT TRIM(SUBSTRING_INDEX(SUBSTRING_INDEX(a.category, ',', numbers.n), ',', -1)) AS category,
                    w.name AS website_name
                FROM articles a
                JOIN websites w ON a.website_id = w.id
                JOIN (
                    SELECT 1 n UNION ALL SELECT 2 UNION ALL SELECT 3 UNION ALL SELECT 4 UNION ALL SELECT 5
                    UNION ALL SELECT 6 UNION ALL SELECT 7 UNION ALL SELECT 8 UNION ALL SELECT 9 UNION ALL SELECT 10
                ) numbers ON CHAR_LENGTH(a.category) - CHAR_LENGTH(REPLACE(a.category, ',', '')) >= numbers.n - 1
            """)

            query_categories = db.session.execute(category_query)
            categories = [{'category': row.category, 'website_name': row.website_name} for row in query_categories.fetchall()]
            
            return render_template('category.html', categories=categories)


        @app.route('/category/<category_name>')
        def category_articles(category_name):
            query_articles = db.session.execute(text('SELECT * FROM articles WHERE category = :category_name'), {'category_name': category_name})
            articles = query_articles.fetchall()
            return render_template('category.html', category_name=category_name, articles=articles)

        @app.route('/contact')
        def contact():
            return render_template('contact.html')

        @app.route('/login', methods=['GET', 'POST'])
        def login():
            if request.method == 'POST':
                email = request.form['email']
                password = request.form['password']
                user = User.query.filter_by(email=email).first()

                if user and check_password_hash(user.password, password):
                    session['user_id'] = user.id
                    session['user_role'] = user.role
                    session['membership'] = user.membership  # Guardar membresía en la sesión
                    return redirect(url_for('dashboard.index'))
                else:
                    flash('Credenciales inválidas. Por favor, intenta de nuevo.')
            return render_template('login.html')



        @app.route('/logout')
        def logout():
            session.pop('user_id', None)
            flash('Has cerrado sesión exitosamente.')
            return redirect(url_for('login'))

        @app.route('/article/<int:article_id>')
        def article_details(article_id):
            article = Article.query.get_or_404(article_id)
            return render_template('single.html', article=article)

   

        @app.route('/edit/<int:id>', methods=['GET', 'POST'])
        def edit_article(id):
            # Obtener el artículo por ID
            article = Article.query.get_or_404(id)

            if request.method == 'POST':
                # Actualizar los valores del artículo con los datos del formulario
                article.title = request.form['title']
                article.url = request.form['url']
                article.date_published = request.form['date_published']
                article.image_url = request.form['image_url']
                article.website_id = request.form['website_id']
                article.description = request.form['description']
                article.category = request.form['category']

                # Guardar los cambios en la base de datos
                db.session.commit()

                # Redirigir al listado de artículos usando el nombre completo del endpoint
                return redirect(url_for('dashboard.list_articles'))

            return render_template('edit_article.html', article=article)

        @app.route('/edituser/<int:id>', methods=['GET', 'POST'])
        def edit_user(id):
            # Obtener el artículo por ID
            user = User.query.get_or_404(id)

            if request.method == 'POST':
                # Actualizar los valores del artículo con los datos del formulario
                user.username = request.form['username']
                user.email = request.form['email']
                user.password = request.form['password']
                user.first_name = request.form['first_name']
                user.last_name = request.form['last_name']
                user.role = request.form['role']
                user.membership = request.form['membership']
                

                # Guardar los cambios en la base de datos
                db.session.commit()

                # Redirigir al listado de artículos usando el nombre completo del endpoint
                return redirect(url_for('dashboard.list_user'))

            return render_template('edit_user.html', user=user)


        @app.route('/delete/<int:id>', methods=['POST'])
        def delete_article(id):
            # Encuentra el artículo por ID
            article = Article.query.get_or_404(id)

            # Elimina el artículo
            db.session.delete(article)
            db.session.commit()

            flash('Article deleted successfully!', 'success')

            # Redirigir al listado de artículos usando el nombre completo del endpoint
            return redirect(url_for('dashboard.list_articles'))

        @app.route('/deleteuser/<int:id>', methods=['POST'])
        def delete_user(id):
            # Encuentra el artículo por ID
            user = User.query.get_or_404(id)

            # Elimina el artículo
            db.session.delete(user)
            db.session.commit()

            flash('User deleted successfully!', 'success')

            # Redirigir al listado de artículos usando el nombre completo del endpoint
            return redirect(url_for('dashboard.list_user'))

        @app.route('/search', methods=['GET'])
        def search():
            query = request.args.get('query', '').strip()  # Obtiene el término de búsqueda
            
            # Busca en la base de datos artículos cuyo título contenga el término de búsqueda
            search_results = db.session.execute(text(
                "SELECT * FROM articles WHERE title LIKE :query OR category LIKE :query"
            ), {'query': f'%{query}%'}).fetchall()
            
            return render_template('search_results.html', query=query, search_results=search_results)


        def periodic_scrape():
            while True:
                
                scrape_main()  # Llama a la función main de scraping.py
                correo_main()  # Llama a la función main de correo.py
                
                time.sleep(350)  # Espera 120 segundos (2 minutos) antes de volver a ejecutar

        # Inicia el hilo para el scraping periódico
        scraping_thread = threading.Thread(target=periodic_scrape, daemon=True)
        scraping_thread.start()

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
