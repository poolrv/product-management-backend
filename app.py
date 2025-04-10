# app.py
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
import os
import time
from datetime import datetime

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes with appropriate headers

# Database configuration - Configuración para Railway
database_url = os.environ.get('DATABASE_URL')
# Si el DATABASE_URL comienza con 'mysql://', cambiamos a 'mysql+pymysql://' para compatibilidad con SQLAlchemy
if database_url and database_url.startswith('mysql://'):
    database_url = database_url.replace('mysql://', 'mysql+pymysql://', 1)

app.config['SQLALCHEMY_DATABASE_URI'] = database_url or 'sqlite:///products.db'  # SQLite como fallback
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Product model
class Product(db.Model):
    __tablename__ = 'products'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

# Health check route
@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy', 'time': time.time()})

# Routes
@app.route('/api/products', methods=['GET'])
def get_products():
    try:
        products = Product.query.all()
        return jsonify([product.to_dict() for product in products])
    except Exception as e:
        app.logger.error(f"Error fetching products: {str(e)}")
        return jsonify({'error': 'Failed to fetch products'}), 500

@app.route('/api/products/<int:product_id>', methods=['GET'])
def get_product(product_id):
    try:
        product = Product.query.get_or_404(product_id)
        return jsonify(product.to_dict())
    except Exception as e:
        app.logger.error(f"Error fetching product {product_id}: {str(e)}")
        return jsonify({'error': f'Failed to fetch product with id {product_id}'}), 500

@app.route('/api/products', methods=['POST'])
def create_product():
    try:
        data = request.get_json()
        
        if not data or 'name' not in data:
            return jsonify({'error': 'Product name is required'}), 400
        
        product = Product(name=data['name'])
        db.session.add(product)
        db.session.commit()
        
        return jsonify(product.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error creating product: {str(e)}")
        return jsonify({'error': 'Failed to create product'}), 500

@app.route('/api/products/<int:product_id>', methods=['PUT'])
def update_product(product_id):
    try:
        product = Product.query.get_or_404(product_id)
        data = request.get_json()
        
        if not data or 'name' not in data:
            return jsonify({'error': 'Product name is required'}), 400
        
        product.name = data['name']
        product.updated_at = datetime.now()
        db.session.commit()
        
        return jsonify(product.to_dict())
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error updating product {product_id}: {str(e)}")
        return jsonify({'error': f'Failed to update product with id {product_id}'}), 500

@app.route('/api/products/<int:product_id>', methods=['DELETE'])
def delete_product(product_id):
    try:
        product = Product.query.get_or_404(product_id)
        db.session.delete(product)
        db.session.commit()
        
        return jsonify({'message': 'Product deleted successfully'})
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error deleting product {product_id}: {str(e)}")
        return jsonify({'error': f'Failed to delete product with id {product_id}'}), 500

# Search products by name
@app.route('/api/products/search', methods=['GET'])
def search_products():
    try:
        query = request.args.get('q', '')
        products = Product.query.filter(Product.name.ilike(f'%{query}%')).all()
        return jsonify([product.to_dict() for product in products])
    except Exception as e:
        app.logger.error(f"Error searching products: {str(e)}")
        return jsonify({'error': 'Failed to search products'}), 500

# Initialize the database - En un contexto de aplicación para mejor manejo de errores
def init_db():
    try:
        with app.app_context():
            db.create_all()
            print("Database tables created successfully")
    except Exception as e:
        print(f"Error creating database tables: {str(e)}")
        # No queremos que falle completamente la aplicación si hay un error inicial
        # Este enfoque permite que la aplicación inicie aunque la DB no esté disponible inmediatamente

# Inicializar la base de datos de manera más segura
init_db()

if __name__ == '__main__':
    # Run the app
    app.run(host='0.0.0.0', port=5000, debug=True)