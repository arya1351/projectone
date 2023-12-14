from flask import Flask, render_template, session, request, redirect, url_for
from models import db, Users, Books, Pesanan
from flask_bcrypt import Bcrypt
from werkzeug.utils import secure_filename
import re
import os

app = Flask(__name__)

app.config['SECRET_KEY'] = 'project1'
app.config["SQLALCHEMY_DATABASE_URI"] = 'mysql+pymysql://root:''@127.0.0.1/sistemperpustakaan'

SQLALCHEMY_TRACK_MODIFICATIONS = False
SQLALCHEMY_ECHO = True

bcrypt = Bcrypt(app)

db.init_app(app)

with app.app_context():
    db.create_all()

app.config['UPLOAD_FOLDER'] = 'static/images'
    
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])

def allowed_file(filename):
 return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    books = Books.query.all()
    
    return render_template('index.html', books = books)

@app.route('/daftarbuku')
def daftarbuku():
    books = Books.query.all()
 
    return render_template("daftarbuku.html", books = books)

@app.route('/dashboardpemesanan')
def dashboardpemesanan():
    pemesanan = Pesanan.query.all()
 
    return render_template("dashboardpemesanan.html", pemesanan = pemesanan)

@app.route("/deletepemesanan", methods =['GET'])
def deletepemesanan():
    if 'loggedin' in session:
        pemesananid = request.args.get('pemesananid')
        pemesanan = Pesanan.query.get(pemesananid)
        db.session.delete(pemesanan)
        db.session.commit()
        return redirect(url_for('dashboardpemesanan'))

@app.template_filter()
def currencyFormat(value):
    value = float(value)
    return "Rp {:,.2f}".format(value)

@app.route('/pemesanan', methods = ['GET','POST'])
def pemesanan():
    msg=""
    if request.method == 'POST':
        namapemesan = request.form['namapemesan'] 
        noidentitas = request.form['noidentitas'] 
        bukusewa = request.form['bukusewa']
        notelepon = request.form['notelepon']  
        pemesan = Pesanan(namapemesan=namapemesan, noidentitas=noidentitas,  bukusewa = bukusewa, notelepon = notelepon)
        db.session.add(pemesan)
        db.session.commit()       
        msg = "berhasil mendaftar!"
    return render_template('pemesanan.html',msg = msg)

@app.route('/register' , methods = [ 'GET','POST'])
def register():
    message=''
    if request.method == 'POST' and 'name' in request.form and 'password' in request.form and 'email' in request.form :
        fullname = request.form['name']
        password = request.form['password']
        email = request.form['email']
        user_exists = Users.query.filter_by(email=email).first() is not None
        # print(fullname)
        # print(password)
        # print(email)
        user_exist = Users.query.filter_by(email = email).first() is not None
        
        if user_exist:
            message = "Email sudah digunakan !"
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            message = 'Email tidak benar !'
        elif not fullname or not password or not email:
            message = "mohon diisi !"
        else:
            hashed_password = bcrypt.generate_password_hash(password)
            new_user = Users(name = fullname, email = email, password = hashed_password)
            db.session.add(new_user)
            db.session.commit()
            message = "Pendaftaran telah berhasil !"
        
        message= 'registerasi telah berhasil !'
    elif request.method == 'POST' :
        message = 'silahkan coba lagi !'
    return render_template('register.html', message = message)

@app.route('/login' , methods = ['GET' , 'POST'])
def login():
    message = ''
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        #print(email)
        #print(password)
        if email == '' or password == '':
            message = 'Please enter email and password !'
        else:
            user = Users.query.filter_by(email=email).first()
            print(user)
 
            if user is None:
                message = 'Please enter correct email / password !'
            else:
                if not bcrypt.check_password_hash(user.password, password):
                    message = 'Please enter correct email and password !'
                else:    
                    session['loggedin'] = True
                    session['userid'] = user.id
                    session['name'] = user.name
                    session['email'] = user.email
                    message = 'Logged in successfully !'           
                    return redirect(url_for('dashboard'))
 
    return render_template('login.html', message = message)

@app.route("/dashboard", methods =['GET', 'POST'])
def dashboard():
    if 'loggedin' in session:        
        return render_template("dashboard.html")
    return redirect(url_for('login')) 
 
@app.route('/logout')
def logout():
    session.pop('loggedin', None)
    session.pop('userid', None)
    session.pop('email', None)
    return redirect(url_for('login'))

@app.route("/buku", methods =['GET', 'POST'])
def books():
    if 'loggedin' in session:
        books = Books.query.all()
 
        return render_template("books.html", books = books)
    return redirect(url_for('login'))
 
@app.route('/save_book',methods=['POST'])
def save_book():
    msg = ''    
    if 'loggedin' in session:
        if request.method == 'POST':
            name = request.form['name'] 
            isbn = request.form['isbn'] 
            hargasewa = request.form['hargasewa']  
            action = request.form['action']
 
            if action == 'updateBook':
                bookid = request.form['bookid']
                book = Books.query.get(bookid)
             
                book.name = name
                book.isbn = isbn
                book.hargasewa = hargasewa
 
                db.session.commit()
                print("UPDATE book") 
            else:
                file = request.files['uploadFile']
                filename = secure_filename(file.filename)
                print(filename)
                if file and allowed_file(file.filename):
                    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                    filenameimage = file.filename
 
                    book = Books(name=name, picture=filenameimage, isbn=isbn, hargasewa = hargasewa)
                    db.session.add(book)
                    db.session.commit()
                    print("INSERT INTO book")  
                else:
                    msg  = 'Invalid Uplaod only png, jpg, jpeg, gif'
            return redirect(url_for('books'))        
        elif request.method == 'POST':
            msg = 'Please fill out the form !'       
        return render_template("books.html", msg = msg)
    return redirect(url_for('login'))
 
@app.route("/edit_book", methods =['GET', 'POST'])
def edit_book():
    msg = ''    
    if 'loggedin' in session:
        bookid = request.args.get('bookid')
        print(bookid)
        books = Books.query.get(bookid)
         
        return render_template("edit_books.html", books = books)
    return redirect(url_for('login'))
 
@app.route("/delete_book", methods =['GET'])
def delete_book():
    if 'loggedin' in session:
        bookid = request.args.get('bookid')
        book = Books.query.get(bookid)
        print(book.picture)
        db.session.delete(book)
        db.session.commit()
        os.unlink(os.path.join(app.config['UPLOAD_FOLDER'], book.picture))
        return redirect(url_for('books'))
    return redirect(url_for('login'))   
 

if __name__=='__main__':
    app.run(debug=True)