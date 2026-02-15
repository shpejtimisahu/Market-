from flask import Flask, render_template, request, redirect, url_for, jsonify,flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import json
import os
from werkzeug.utils import secure_filename


app = Flask(__name__)
PRODUCTS_FILE = 'products.json'
app.secret_key = 'sekret'

USERS_FILE = 'users.json'

def load_products():
    if not os.path.exists(PRODUCTS_FILE):
        return []
    with open(PRODUCTS_FILE, 'r') as f:
        return json.load(f)

def save_products(products):
    with open(PRODUCTS_FILE, 'w') as f:
        json.dump(products, f, indent=2)

@app.route('/')
def index():

    category = request.args.get('category', '').strip().lower()

    all_products = load_products()


    if category:
        products = [p for p in all_products if p.get('category', '').strip().lower() == category]
    else:
        products = all_products

    categories = sorted(list({p.get('category', '').strip() for p in all_products if p.get('category')}))

    return render_template('index.html',
                           products=products,
                           selected_category=category,
                           categories=categories)


@app.route('/product/<int:product_id>')
def product_detail(product_id):
    products = load_products()
    product = next((p for p in products if p['id'] == product_id), None)
    if not product:
        return "Produkti nuk u gjet", 404
    return render_template('product_detail.html', product=product)




@app.route('/delete/<int:product_id>', methods=['POST'])
@login_required
def delete_product(product_id):
    products = load_products()
    product = next((p for p in products if p['id'] == product_id), None)

    if not product:
        return "Produkti nuk ekziston!", 404


    if product.get('user_id') != current_user.id:
        return "Nuk mund të fshish produktin e dikujt tjetër!", 403


    products = [p for p in products if p['id'] != product_id]
    save_products(products)

    return redirect(url_for('index'))




@app.route('/add', methods=['GET', 'POST'])
@login_required
def add_product():
    if request.method == 'POST':
        name = request.form.get('name').strip()
        price = request.form.get('price').strip()
        description = request.form.get('description', '').strip()
        category = request.form.get('category')

        if not name or not price:
            return "Emri dhe çmimi janë të detyrueshëm!", 400

        try:
            price = float(price)
            if price < 0:
                return "Çmimi duhet të jetë numër pozitiv.", 400
        except ValueError:
            return "Çmimi duhet të jetë numër i vlefshëm.", 400

        image_file = request.files.get('image')
        image_url = request.form.get('image_url', '').strip()

        image_filename = None

        if image_file and image_file.filename != '':
            filename = secure_filename(image_file.filename)
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            image_file.save(image_path)
            image_filename = f"/static/uploads/{filename}"
        elif image_url:
            image_filename = image_url

        products = load_products()
        new_product = {
            'id': len(products) + 1,
            'name': name,
            'price': price,
            'description': description,
            'image': image_filename,
            'category': category,
            'user_id': current_user.id
        }

        products.append(new_product)
        save_products(products)

        return redirect(url_for('index'))

    return render_template('add_product.html')





def load_users():
    if not os.path.exists(USERS_FILE):
        return []
    with open(USERS_FILE, 'r') as f:
        return json.load(f)

def save_users(users):
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f, indent=2)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username').strip()
        email = request.form.get('email').strip()
        password = request.form.get('password').strip()

        if not username or not email or not password:
            flash('Të gjitha fushat janë të detyrueshme.', 'danger')
            return redirect(url_for('register'))

        users = load_users()

        if any(u['email'] == email or u['username'] == username for u in users):
            flash('Ky përdorues ose email ekziston.', 'warning')
            return redirect(url_for('register'))

        new_user = {
            'id': len(users) + 1,
            'username': username,
            'email': email,
            'password': password
        }

        users.append(new_user)
        save_users(users)
        flash('Regjistrimi u krye me sukses!', 'success')
        return redirect(url_for('index'))

    return render_template('register.html')


app.secret_key = 'sekreti_yt'

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


from flask_login import UserMixin

class User(UserMixin):
    def __init__(self, id):
        self.id = str(id)



@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        users = load_users()

        for u in users:
            if u['email'] == email and u['password'] == password:
                users = load_users()
                for u in users:
                    if u['email'] == email and u['password'] == password:
                        user = User(u['id'])
                        login_user(user)
                        # flash("U kyqet me sukses!", "success")
                        return redirect(url_for('index'))

        flash("Email ose fjalëkalim i pasaktë!", "danger")

    return render_template('login.html')

def get_user_data(user_id):
    users = load_users()
    for u in users:
        if str(u['id']) == str(user_id):
            return u
    return None


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@login_manager.user_loader
def load_user(user_id):
    return User(user_id)



UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


if __name__ == '__main__':
    app.run(debug=True)

