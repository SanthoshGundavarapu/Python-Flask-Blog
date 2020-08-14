import json
import os

from flask import Flask, render_template, session, redirect
from flask import request
from flask_mail import Mail
from flask_sqlalchemy import SQLAlchemy
# from werkzeug import secure_filename
from werkzeug.utils import secure_filename
import math


local_server = True
with open('config.json', 'r') as c:
    params = json.load(c)["params"]

app = Flask(__name__)
app.secret_key = 'super-secret-key'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER']= params['upload_location']
app.config.update(
    MAIL_SERVER='smtp.gmail.com',
    MAIL_PORT='465',
    MAIL_USE_SSL=True,
    MAIL_USERNAME=params['gmail-user'],
    MAIL_PASSWORD=params['password']

)
mail = Mail(app)
if (local_server):
    app.config['SQLALCHEMY_DATABASE_URI'] = params['local_uri']  # 'mysql://root:123456@localhost/my_show'
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = params['prod_uri']  # mysql://root:123456@localhost/my_show

db = SQLAlchemy(app)


class contacts(db.Model):
    # sno,name,phone_num,email,msg,date
    sno = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=False, nullable=False)
    phone_num = db.Column(db.String(12), nullable=False)
    email = db.Column(db.String(20))
    msg = db.Column(db.String(120), nullable=False)
    # date = db.Column(db.String(12), nullable=False)


class posts(db.Model):
    # sno,name,phone_num,email,msg,date
    sno = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80), unique=False, nullable=False)
    content = db.Column(db.String(120), nullable=False)
    slug = db.Column(db.String(20))
    img_file = db.Column(db.String(120), nullable=False)
    tag_line = db.Column(db.String(100))
    # msg= db.Column(db.String(120), nullable=False)
    # date = db.Column(db.String(12), nullable=False)


#pagination logic
@app.route('/')
def home_1():
    posts_1=posts.query.filter_by().all()
    last=math.ceil(len(posts_1)/int(params['no_of_posts']))
    page= request.args.get('page')
    if not str(page).isnumeric():
        page = 1
    #logic
    #slicing of posts page wise
    page=int(page)
    posts_1=posts_1[(page-1)*int(params['no_of_posts']) :(page-1)*int(params['no_of_posts'])+int(params['no_of_posts'])]
    if page==1:
        prev='#'
        next="/?page="+str(page+1)
    elif page==last:
        prev="/?page="+str(page-1)
        next="#"
    else:
        prev="/?page="+str(page-1)
        next="/?page="+str(page+1)

    return render_template('index.html',params=params,posts_1=posts_1,prev=prev,next=next)


#@app.route('/')
#def home():
   # posts_1 = posts.query.filter_by().all()
    #return render_template('index.html', params=params, posts_1=posts_1)


@app.route("/dashboard", methods=['GET', 'POST'])
def dashboard():
    if 'user' in session:
        if session['user'] == params['admin_user']:
            post = posts.query.all()
            return render_template('dashboard_loggedin.html', params=params,post=post)

    if request.method == 'POST':
        username = request.form.get('uname')
        password = request.form.get('pass')
        if username == params['admin_user'] and password == params["pass"]:
            session['user'] = username
            post = posts.query.all()
            return render_template('dashboard_loggedin.html', params=params,post=post)
    # REDIRECT TO ADMIN PANEL
    return render_template('login.html', params=params)

#adding functionality to edit button of admin panel
@app.route('/edit/<string:sno>', methods = ['GET', 'POST'])
def edit(sno):
    #firstly we check user is in session or logged in
    if 'user' in session:
        if session['user'] == params['admin_user']:
            if request.method == 'POST':
                title= request.form.get('title')
                tag_line=request.form.get('tag_line')
                slug=request.form.get('slug')
                content=request.form.get('content')
                img_file=request.form.get('img_file')

                if sno =='0':
                    post=posts(title=title, content=content, slug=slug, img_file=img_file, tag_line=tag_line)
                    db.session.add(post)
                    db.session.commit()
                else:
                    post=posts.query.filter_by(sno=sno).first()
                    post.title=title
                    post.content= content
                    post.slug=slug
                    post.img_file=img_file
                    post.tag_line=tag_line
                    db.session.commit()
                    return redirect('/edit/'+sno)
            post=posts.query.filter_by(sno=sno).first()
            return render_template('edit.html', params=params,sno=sno,post=post)


#file upload endpoint handling function
@app.route('/uploader',methods=['GET','POST'])
def file_uploader():
    #firstly check whether user is logged in or not
    if 'user' in session:
        if session['user'] == params['admin_user']:
            if request.method=='POST':
                f=request.files['file']
                f.save(os.path.join(app.config['UPLOAD_FOLDER'],secure_filename(f.filename)))
                return 'uploaded successfully'

#making delete button functional
@app.route('/delete/<string:sno>',methods=['GET','POST'])
def delete(sno):
    #firstly check whether user is logged in or not
    if 'user' in session:
        if session['user'] == params['admin_user']:
            post=posts.query.filter_by(sno=sno).first()
            db.session.delete(post)
            db.session.commit()
    return redirect('/dashboard')


@app.route('/about')
def about():
    return render_template('about.html', params=params)


@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if (request.method == 'POST'):
        ''' add entry to database.'''

        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        message = request.form.get('message')
        # sno,name,phone_num,email,msg,date
        entry = contacts(name=name, phone_num=phone, msg=message, email=email)
        db.session.add(entry)
        db.session.commit()
        mail.send_message('his this' + name,
                          sender=email,
                          recipients=[params['gmail-user']],
                          body=message + "\n" + phone)

    return render_template('contact.html', params=params)


@app.route("/post/<string:post_slug>", methods=['GET'])
def post_route(post_slug):
    post = posts.query.filter_by(slug=post_slug).first()

    return render_template('post.html', params=params, post=post)








@app.route('/post')
def post_1():
    return render_template('post.html', params=params)


app.run(debug=True)
