from flask import Flask, render_template, redirect, request, abort, url_for
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
import os
from sqlalchemy.sql import func
from werkzeug.utils import secure_filename
from forms.news import NewsForm
from forms.user import RegisterForm, LoginForm
from data.news import News, Rating
from data.users import User
from data import db_session

app = Flask(__name__)
login_manager = LoginManager()
login_manager.init_app(app)
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    return db_sess.query(User).get(user_id)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect("/")


def main():
    db_session.global_init("db/blogs.db")
    app.run()


@app.route('/addstory', methods=['GET', 'POST'])
@login_required
def add_news():
    form = NewsForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        news = News()
        news.title = form.title.data
        news.content = form.content.data
        news.is_private = form.is_private.data

        if form.file.data:
            file = form.file.data
            filename = secure_filename(file.filename)
            upload_dir = os.path.join('static', 'uploads')  
            os.makedirs(upload_dir, exist_ok=True)
            file_path = os.path.join(upload_dir, filename)
            file.save(file_path)

            db_path = os.path.join('uploads', filename).replace('\\', '/')
            news.file_path = db_path  

        current_user.news.append(news)
        db_sess.merge(current_user)
        db_sess.commit()
        return redirect('/')
    return render_template('news.html', title='Новый рассказ', form=form)


@app.route('/story_delete/<int:id>', methods=['GET', 'POST'])
@login_required
def news_delete(id):
    db_sess = db_session.create_session()
    news = db_sess.query(News).filter(News.id == id, News.user == current_user).first()
    if news:
        db_sess.delete(news)
        db_sess.commit()
    else:
        abort(404)
    return redirect('/')


@app.route('/storyedit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_news(id):
    form = NewsForm()
    if request.method == "GET":
        db_sess = db_session.create_session()
        news = db_sess.query(News).filter(News.id == id, News.user == current_user).first()
        if news:
            form.title.data = news.title
            form.content.data = news.content
            form.is_private.data = news.is_private
        else:
            abort(404)
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        news = db_sess.query(News).filter(News.id == id, News.user == current_user).first()
        if news:
            news.title = form.title.data
            news.content = form.content.data
            news.is_private = form.is_private.data
            if form.file.data:
                file = form.file.data
                filename = secure_filename(file.filename)
                upload_dir = os.path.join('static', 'uploads')  
                os.makedirs(upload_dir, exist_ok=True)
                file_path = os.path.join(upload_dir, filename)
                file.save(file_path)
                db_path = os.path.join('uploads', filename).replace('\\', '/')
                news.file_path = db_path  
            db_sess.merge(current_user)
            db_sess.commit()
            return redirect('/')
        else:
            abort(404)
    return render_template('news.html', title='Редактирование рассказа', form=form)


@app.route("/")
def index():
    sort = request.args.get('sort', 'newest')
    db_sess = db_session.create_session()
    
    query = db_sess.query(News)
    
    if current_user.is_authenticated:
        query = query.filter((News.user == current_user) | (News.is_private != True))
    else:
        query = query.filter(News.is_private != True)
    
    if sort == 'top':
        query = query.outerjoin(Rating).group_by(News.id).order_by(
            func.coalesce(func.sum(Rating.value), 0).desc())
    else:
        query = query.order_by(News.created_date.desc())
    
    news = query.all()
    return render_template("index.html", news=news)


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        if form.password.data != form.password_again.data:
            return render_template('register.html', title='Регистрация', form=form,
                                   message="Пароли не совпадают")
        db_sess = db_session.create_session()
        if db_sess.query(User).filter(User.email == form.email.data).first():
            return render_template('register.html', title='Регистрация', form=form,
                                   message="Такой пользователь уже есть")
        user = User(
            name=form.name.data,
            email=form.email.data,
        )
        user.set_password(form.password.data)
        db_sess.add(user)
        db_sess.commit()
        return redirect('/login')
    return render_template('register.html', title='Регистрация', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.email == form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            return redirect("/")
        return render_template('login.html', message="Неправильный логин или пароль", form=form)
    return render_template('login.html', title='Авторизация', form=form)

@app.route('/rate/<int:news_id>/<int:value>')
@login_required
def rate(news_id, value):
    db_sess = db_session.create_session()
    
    existing = db_sess.query(Rating).filter(
        Rating.user_id == current_user.id,
        Rating.news_id == news_id
    ).first()
    
    if existing:
        existing.value = value
    else:
        rating = Rating(
            user_id=current_user.id,
            news_id=news_id,
            value=value
        )
        db_sess.add(rating)
    
    db_sess.commit()
    return redirect(request.referrer or url_for('index'))

@app.route('/story/<int:id>')
def story(id):
    db_sess = db_session.create_session()
    news = db_sess.query(News).filter(News.id == id).first()
    if not news:
        abort(404)
    return render_template('storyreader.html', title=news.title, news=news)

@app.route("/yourstorys")
def yourstor():
    sort = request.args.get('sort', 'newest')
    db_sess = db_session.create_session()
    
    query = db_sess.query(News)
    
    if current_user.is_authenticated:
        query = query.filter((News.user == current_user) | (News.is_private != True))
    else:
        query = query.filter(News.is_private != True)
    
    if sort == 'top':
        query = query.outerjoin(Rating).group_by(News.id).order_by(
            func.coalesce(func.sum(Rating.value), 0).desc())
    else:
        query = query.order_by(News.created_date.desc())
    
    news = query.all()
    return render_template("yours.html", news=news)

if __name__ == '__main__':
    main()
