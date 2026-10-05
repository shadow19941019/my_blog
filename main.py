from datetime import datetime
from functools import wraps

import werkzeug.security
from flask import Flask, abort, flash, redirect, render_template, request, url_for
from flask_bootstrap import Bootstrap
from flask_ckeditor import CKEditor
from flask_login import LoginManager, UserMixin, current_user, login_required, login_user, logout_user
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey, Integer, String, Text
from werkzeug.security import check_password_hash, generate_password_hash
from forms import CommentForm, CreatePostForm, LoginForm, RegisterForm


class Base(DeclarativeBase):
    pass


app = Flask(__name__)
app.config['SECRET_KEY'] = 'change-this-in-a-real-project'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///posts.db'

db = SQLAlchemy(model_class=Base)
db.init_app(app)
Bootstrap(app)
ckeditor = CKEditor(app)

login_manager = LoginManager()
login_manager.init_app(app)


class User(UserMixin, db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    password: Mapped[str] = mapped_column(String(255), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    blog_posts = relationship("BlogPost", back_populates="author")
    comments = relationship("Comment", back_populates="reader")


class BlogPost(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(250), unique=True, nullable=False)
    subtitle: Mapped[str] = mapped_column(String(250), nullable=False)
    date: Mapped[str] = mapped_column(String(250), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    img_url: Mapped[str] = mapped_column(String(250), nullable=False)
    author_id: Mapped[int] = mapped_column(Integer, ForeignKey("user.id"))
    author = relationship("User", back_populates="blog_posts")
    comments = relationship("Comment", back_populates="parent_post")


class Comment(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    reader_id: Mapped[int] = mapped_column(Integer, ForeignKey("user.id"))
    reader = relationship("User", back_populates="comments")
    parent_post_id: Mapped[int] = mapped_column(Integer, ForeignKey("blog_post.id"))
    parent_post = relationship("BlogPost", back_populates="comments")


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


def admin_only(function):
    @wraps(function)
    def decorated_function(*args, **kwargs):
        if current_user.id == 1:
            return function(*args, **kwargs)
        else:
            abort(403)  # Cseréld le valódi jogosultság-ellenőrzésre.

    return decorated_function


@app.route('/')
def get_all_posts():
    posts = db.session.execute(db.select(BlogPost)).scalars().all()
    return render_template('index.html', all_posts=posts, current_user=current_user)


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        email = form.email.data
        password = werkzeug.security.generate_password_hash(form.password.data, method="pbkdf2:sha256", salt_length=8)
        name = form.name.data
        new_user = User(
            email=email,
            password=password,
            name=name
        )
        if db.session.query(User).filter_by(email=email).first():
            flash("Email already exists!")
            return redirect(url_for('login'))
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)
        return redirect(url_for('get_all_posts'))
    return render_template('register.html', form=form, current_user=current_user)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = db.session.query(User).filter_by(email=form.email.data).first()
        if user:
            if check_password_hash(user.password, form.password.data):
                login_user(user)
                return redirect(url_for('get_all_posts'))
            flash("Invalid username or password")
            return redirect(url_for('login'))
        flash('Not a valid username or password')
    return render_template('login.html', form=form, current_user=current_user)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('get_all_posts'))


@app.route('/post/<int:post_id>', methods=['GET', 'POST'])
def show_post(post_id):
    requested_post = db.session.query(BlogPost).filter_by(id=post_id).first()
    form = CommentForm()
    if request.method == 'POST':
        if current_user.is_authenticated:
            if form.validate_on_submit():
                comment = Comment(
                    text=form.comment_text.data,
                    reader=current_user,
                    parent_post=requested_post
                )
                db.session.add(comment)
                db.session.commit()
                return redirect(url_for('show_post',post_id=requested_post.id))
        else:
            flash("Please login to comment")
            return redirect(url_for('login'))
    return render_template('post.html', post=requested_post, form=form, current_user=current_user)


@app.route('/new-post', methods=['GET', 'POST'])
@login_required
@admin_only
def add_new_post():
    form = CreatePostForm()
    if current_user.id == 1:
        if form.validate_on_submit():
            new_post = BlogPost(
                title=form.title.data,
                subtitle=form.subtitle.data,
                date=datetime.now().strftime("%B %d, %Y"),
                body=form.body.data,
                img_url=form.img_url.data,
                author=current_user
            )
            db.session.add(new_post)
            db.session.commit()
            return redirect(url_for('show_post', post=new_post, form=form, post_id=new_post.id))
    return render_template('make-post.html', form=form, current_user=current_user)


@app.route('/edit-post/<int:post_id>', methods=['GET', 'POST'])
@login_required
@admin_only
def edit_post(post_id):
    post = db.session.query(BlogPost).filter_by(id=post_id).first()
    form = CreatePostForm()
    if form.validate_on_submit():
        post.title = form.title.data
        post.subtitle = form.subtitle.data
        post.body = form.body.data
        post.img_url = form.img_url.data
        post.date = datetime.now().strftime("%B %d, %Y")
        db.session.commit()
        return redirect(url_for('show_post', post=post, form=form, post_id=post_id))

    return render_template('make-post.html', form=form, is_edit=True, current_user=current_user)


@app.route('/delete/<int:post_id>')
@login_required
@admin_only
def delete_post(post_id):
    # TODO 11: admin-jogosultsággal töröld a bejegyzést.
    abort(501)


@app.route('/about')
def about():
    return render_template('about.html', current_user=current_user)


@app.route('/contact')
def contact():
    return render_template('contact.html', current_user=current_user)


with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)
