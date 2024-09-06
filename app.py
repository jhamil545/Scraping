from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text  # Importa la función text



app = Flask(__name__)

# Configura la base de datos MySQL
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:@localhost/newspaper'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Define el modelo 'Article' para la tabla 'articles'
class Article(db.Model):
    __tablename__ = 'articles'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    url = db.Column(db.String(255))
    date_published = db.Column(db.DateTime)
    image_url = db.Column(db.String(255))
    category_id = db.Column(db.Integer)
    website_id = db.Column(db.Integer)
    description = db.Column(db.Text)
    category = db.Column(db.String(50))

    def __repr__(self):
        return f'<Article {self.title}>'

# Ruta para la página principal
@app.route('/')
def home():
    # Consulta para obtener categorías únicas
    query_categories = db.session.execute(text('SELECT DISTINCT category FROM articles'))
    categories = [row[0] for row in query_categories.fetchall()]

    # Otra consulta para obtener artículos recientes
    query_recent_articles = db.session.execute(text('SELECT * FROM articles ORDER BY date_published DESC LIMIT 5'))
    recent_articles = query_recent_articles.fetchall()

    # Consulta para obtener artículos por categoría
    articles_by_category = {}
    for category in categories:
        query_articles = db.session.execute(text('SELECT * FROM articles WHERE category = :category'), {'category': category})
        articles_by_category[category] = query_articles.fetchall()

    return render_template('index.html', categories=categories, recent_articles=recent_articles,articles_by_category=articles_by_category)


# Ruta para la página de categorías
@app.route('/category')
def category():
    # Consulta para obtener categorías únicas
    query_categories = db.session.execute(text('SELECT DISTINCT category FROM articles'))
    categories = [row[0] for row in query_categories.fetchall()]

   

    # Renderiza la plantilla y pasa las categorías
    return render_template('category.html', categories=categories,)

@app.route('/category/<category_name>')
def category_articles(category_name):
    print(f"Category Name: {category_name}")  # Verifica el valor de category_name
    query_articles = db.session.execute(text('SELECT * FROM articles WHERE category = :category_name'), {'category_name': category_name})
    articles = query_articles.fetchall()
    print(f"Articles: {articles}")  # Verifica los artículos recuperados

    return render_template('category.html', category_name=category_name, articles=articles)


# Ruta para la página de contacto
@app.route('/contact')
def contact():
    return render_template('contact.html')

# Ruta para la página de detalles del artículo
@app.route('/article/<int:article_id>')
def article_details(article_id):
    article = Article.query.get_or_404(article_id)
    return render_template('single.html', article=article)




if __name__ == '__main__':
    app.run(debug=True)
