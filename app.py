from flask import Flask, request, render_template, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
import datetime

app = Flask(__name__)
app.secret_key = 'This is a random secret key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///dough.db'
db = SQLAlchemy(app)

SCOOP_SIZE = .01

# =========================== DB ===========================

class User(db.Model):
    id = db.Column(db.Integer, nullable=False, primary_key=True)
    first_name = db.Column(db.String, nullable=False)
    last_name = db.Column(db.String, nullable=False)
    email = db.Column(db.String, nullable=False)
    password = db.Column(db.String, nullable=False)
    sales = db.relationship('Sale')

class Dough(db.Model):
    id = db.Column(db.Integer, nullable=False, primary_key=True)
    type = db.Column(db.String, nullable=False)
    price_per = db.Column(db.Float, nullable=False)
    qty = db.Column(db.Float, nullable=False)
    date_made = db.Column(db.DateTime, nullable=False)
    active = db.Column(db.Boolean, default=True)

sale_doughs = db.Table('sale_doughs',
    db.Column('dough_id', db.Integer, db.ForeignKey('dough.id'), primary_key=True), 
    db.Column('sale_id', db.Integer, db.ForeignKey('sale.id'), primary_key=True)              
)

class Sale(db.Model):
    id = db.Column(db.Integer, nullable=False, primary_key=True)
    user = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    total = db.Column(db.Float, nullable=False)
    date = db.Column(db.DateTime, nullable=False)
    doughs = db.relationship('Dough', secondary=sale_doughs, backref='doughs')

with app.app_context():
    db.create_all()

# =========================== DB ===========================
# ========================= ROUTES =========================

@app.route('/', methods = ['GET', 'POST'])
def login():
    if request.method == "POST":
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email = email, password = password).first()
        if user:
            session['user_id'] = user.id
            session['logged_in'] = True
            return redirect(url_for('home'))
        else:
            return redirect(url_for('login'))
    return render_template('login.html')

@app.route('/register', methods = ['GET', 'POST'])
def register():
    if request.method == "POST":
        email = request.form.get('email')
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        password = request.form.get('password')
        new_user = User(email = email, first_name = first_name, last_name = last_name, password = password)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/home', methods=['GET'])
def home():
    user = User.query.get(session['user_id'])
    doughs = Dough.query.filter_by(active=True)
    now = datetime.datetime.now()
    return render_template('home.html', user = user, doughs=doughs, now=now)

@app.route('/logout', methods=["GET"])
def logout():
    session['logged_in'] = False
    return redirect(url_for('login'))

@app.route('/manage', methods=["GET", "POST"])
def manage():
    if request.method == "POST":
        type_of = request.form.get('type')
        price_per = request.form.get('price_per')
        qty = request.form.get('qty')
        date_made = datetime.datetime.now()
        active = True
        new_dough = Dough(type=type_of, price_per=price_per, qty=qty, date_made=date_made, active=active)
        db.session.add(new_dough)
        db.session.commit()
        return redirect(url_for('manage'))
    active_doughs = Dough.query.filter_by(active = True)
    past_doughs = Dough.query.filter_by(active = False)
    return render_template('manage.html', active_doughs=active_doughs, now=datetime.datetime.now(), past_doughs=past_doughs)

@app.route('/edit-dough/<id>', methods=['GET', 'POST'])
def edit_dough(id):
    edit_dough = Dough.query.get(id)
    if request.method == "POST":
        edit_dough.type = request.form.get('type')
        edit_dough.price_per = request.form.get('price_per')
        edit_dough.qty = request.form.get('qty')
        db.session.commit()
        return redirect(url_for('manage'))
    return render_template('edit_dough.html', dough=edit_dough)

@app.route('/change-dough-status/<id>', methods=["GET"])
def change_dough_status(id):
    dough = Dough.query.get(id)
    if dough.active:
        dough.qty = 0
        dough.active = False
    else:
        dough.date_made = datetime.datetime.now()
        dough.active = True
    db.session.commit()
    return redirect(url_for('manage'))

@app.route('/delete-dough/<id>', methods=['GET'])
def delete_dough(id):
    dough = Dough.query.get(id)
    db.session.delete(dough)
    db.session.commit()
    return redirect(url_for('manage'))

@app.route('/sale', methods=["GET", "POST"])
def sale():
    doughs = Dough.query.filter_by(active=True)
    if request.method == "POST":
        sale = Sale(user = User.query.get(session['user_id']).id, total = float(request.form.get('total')), date = datetime.datetime.now())
        for k, v in request.form.items():
            if float(v) > 0 and k != 'total':
                dough = Dough.query.filter_by(type=k).first()
                dough.qty -= SCOOP_SIZE * float(v)
                sale.doughs.append(dough)
        db.session.add(sale)
        db.session.commit()
        return redirect(url_for('sale'))
    return render_template("sale.html", doughs=doughs)

@app.route('/user-sales', methods=["GET"])
def user_sales():
    users = User.query.all()
    return render_template('user_sales.html', users=users)

# ========================= ROUTES =========================

if __name__ == '__main__':
    app.run(debug=True, port=5000)

