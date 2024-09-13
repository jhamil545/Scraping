from flask import Flask, render_template, request, redirect, url_for, flash, session
from models import db, User, Article  # Asegúrate de que estos modelos estén definidos en models.py
from config import Config
from sqlalchemy import text
from werkzeug.security import check_password_hash
import threading
import time
from scraping import main as scrape_main

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
            query_categories = db.session.execute(text('SELECT DISTINCT category FROM articles'))
            categories = [row[0] for row in query_categories.fetchall()]

            query_recent_articles = db.session.execute(text('SELECT * FROM articles ORDER BY date_published DESC LIMIT 5'))
            recent_articles = query_recent_articles.fetchall()

            articles_by_category = {}
            for category in categories:
                query_articles = db.session.execute(text('SELECT * FROM articles WHERE category = :category'), {'category': category})
                articles_by_category[category] = query_articles.fetchall()

            return render_template('index.html', categories=categories, recent_articles=recent_articles, articles_by_category=articles_by_category)

        @app.route('/category')
        def category():
            query_categories = db.session.execute(text('SELECT DISTINCT category FROM articles'))
            categories = [row[0] for row in query_categories.fetchall()]
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
                    return redirect(url_for('dashboard.index'))  # Asegúrate de que este endpoint existe en el Blueprint
                else:
                    flash('Invalid login credentials. Please try again.')
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

        @app.route('/list_articles')
        def list_articles():
            # Lógica para listar artículos, si tienes una base de datos, obtén los artículos aquí
            return render_template('listarticles.html')


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

                return redirect(url_for('list_articles'))

            return render_template('edit_article.html', article=article)

        @app.route('/delete/<int:id>', methods=['POST'])
        def delete_article(id):
            # Encuentra el artículo por ID
            article = Article.query.get_or_404(id)

            # Elimina el artículo
            db.session.delete(article)
            db.session.commit()

            flash('Article deleted successfully!', 'success')
            return redirect(url_for('list_articles'))


        def periodic_scrape():
            while True:
                scrape_main()  # Llama a la función main de scraping.py
                time.sleep(120)  # Espera 120 segundos (2 minutos) antes de volver a ejecutar

        # Inicia el hilo para el scraping periódico
        scraping_thread = threading.Thread(target=periodic_scrape, daemon=True)
        scraping_thread.start()

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
