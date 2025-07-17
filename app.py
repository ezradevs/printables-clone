import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)
csrf = CSRFProtect(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'uploads'

db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    bio = db.Column(db.Text, nullable=True)
    avatar = db.Column(db.String(120), nullable=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Model(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, nullable=False)
    filename = db.Column(db.String(120), nullable=False)
    image_filename = db.Column(db.String(120), nullable=True)
    tags = db.Column(db.String(200), nullable=True)
    upload_date = db.Column(db.DateTime, server_default=db.func.now())
    downloads = db.Column(db.Integer, default=0)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', backref=db.backref('models', lazy=True))

class Favourite(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    model_id = db.Column(db.Integer, db.ForeignKey('model.id'), nullable=False)
    user = db.relationship('User', backref=db.backref('favourites', lazy=True))
    model = db.relationship('Model', backref=db.backref('favourited_by', lazy=True))

class Collection(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', backref=db.backref('collections', lazy=True))

class CollectionItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    collection_id = db.Column(db.Integer, db.ForeignKey('collection.id'), nullable=False)
    model_id = db.Column(db.Integer, db.ForeignKey('model.id'), nullable=False)
    collection = db.relationship('Collection', backref=db.backref('items', lazy=True, cascade="all, delete-orphan"))
    model = db.relationship('Model', backref=db.backref('collection_items', lazy=True))

class Download(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    model_id = db.Column(db.Integer, db.ForeignKey('model.id'), nullable=False)
    timestamp = db.Column(db.DateTime, server_default=db.func.now())
    user = db.relationship('User', backref=db.backref('downloads', lazy=True))
    model = db.relationship('Model', backref=db.backref('downloaded_by', lazy=True))

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, server_default=db.func.now())
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    model_id = db.Column(db.Integer, db.ForeignKey('model.id'), nullable=False)
    user = db.relationship('User', backref=db.backref('comments', lazy=True))
    model = db.relationship('Model', backref=db.backref('comments', lazy=True, cascade="all, delete-orphan"))

from flask import render_template, request, redirect, url_for, flash, session, send_from_directory
from werkzeug.utils import secure_filename

@app.context_processor
def inject_user():
    if 'user_id' in session:
        return {'current_user': User.query.get(session['user_id'])}
    return {'current_user': None}

# ... (existing code) ...

@app.route('/')
def index():
    query = request.args.get('q')
    if query:
        models = Model.query.filter(
            db.or_(
                Model.title.ilike(f'%{query}%'),
                Model.tags.ilike(f'%{query}%')
            )
        ).all()
    else:
        models = Model.query.all()
    return render_template('index.html', models=models)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if User.query.filter_by(username=username).first():
            flash('Username already exists.')
            return redirect(url_for('signup'))
        new_user = User(username=username)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        flash('Account created successfully. Please log in.')
        return redirect(url_for('login'))
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            session['user_id'] = user.id
            flash('Logged in successfully.')
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password.')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('Logged out successfully.')
    return redirect(url_for('index'))

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if 'user_id' not in session:
        flash('Please log in to upload models.')
        return redirect(url_for('login'))

    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        tags = request.form['tags']
        model_file = request.files['model_file']
        image_file = request.files.get('image_file')

        if model_file and model_file.filename != '':
            model_filename = secure_filename(model_file.filename)
            model_file.save(os.path.join(app.config['UPLOAD_FOLDER'], model_filename))

            image_filename = None
            if image_file and image_file.filename != '':
                image_filename = secure_filename(image_file.filename)
                image_file.save(os.path.join(app.config['UPLOAD_FOLDER'], image_filename))

            new_model = Model(
                title=title,
                description=description,
                tags=tags,
                filename=model_filename,
                image_filename=image_filename,
                user_id=session['user_id']
            )
            db.session.add(new_model)
            db.session.commit()
            flash('Model uploaded successfully.')
            return redirect(url_for('index'))

    return render_template('upload.html')

@app.route('/model/<int:model_id>')
def model_detail(model_id):
    model = Model.query.get_or_404(model_id)
    return render_template('model_detail.html', model=model)

@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/download/<int:model_id>')
def download(model_id):
    model = Model.query.get_or_404(model_id)
    model.downloads += 1

    if 'user_id' in session:
        download_entry = Download(user_id=session['user_id'], model_id=model_id)
        db.session.add(download_entry)

    db.session.commit()
    return send_from_directory(app.config['UPLOAD_FOLDER'], model.filename, as_attachment=True)

@app.route('/user/<username>')
def user_profile(username):
    user = User.query.filter_by(username=username).first_or_404()
    total_downloads = db.session.query(db.func.sum(Model.downloads)).filter_by(user_id=user.id).scalar() or 0
    return render_template('user_profile.html', user=user, total_downloads=total_downloads)

@app.route('/favourite/<int:model_id>', methods=['POST'])
def favourite(model_id):
    if 'user_id' not in session:
        return {'status': 'error', 'message': 'You must be logged in to favourite a model.'}, 401

    model = Model.query.get_or_404(model_id)
    favourite = Favourite.query.filter_by(user_id=session['user_id'], model_id=model_id).first()

    if favourite:
        db.session.delete(favourite)
        db.session.commit()
        return {'status': 'success', 'action': 'unfavourited'}
    else:
        new_favourite = Favourite(user_id=session['user_id'], model_id=model_id)
        db.session.add(new_favourite)
        db.session.commit()
        return {'status': 'success', 'action': 'favourited'}

@app.route('/profile/edit', methods=['GET', 'POST'])
def edit_profile():
    if 'user_id' not in session:
        flash('Please log in to edit your profile.')
        return redirect(url_for('login'))

    user = User.query.get_or_404(session['user_id'])

    if request.method == 'POST':
        user.username = request.form['username']
        user.bio = request.form['bio']

        avatar_file = request.files.get('avatar')
        if avatar_file and avatar_file.filename != '':
            avatar_filename = secure_filename(avatar_file.filename)
            avatar_file.save(os.path.join(app.config['UPLOAD_FOLDER'], avatar_filename))
            user.avatar = avatar_filename

        db.session.commit()
        flash('Profile updated successfully.')
        return redirect(url_for('user_profile', username=user.username))

    return render_template('edit_profile.html', user=user)

@app.route('/collection/create', methods=['POST'])
def create_collection():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    name = request.form.get('name')
    if name:
        new_collection = Collection(name=name, user_id=session['user_id'])
        db.session.add(new_collection)
        db.session.commit()
        flash('Collection created successfully.')

    return redirect(url_for('user_profile', username=User.query.get(session['user_id']).username))

@app.route('/collection/<int:collection_id>')
def view_collection(collection_id):
    collection = Collection.query.get_or_404(collection_id)
    return render_template('collection_detail.html', collection=collection)

@app.route('/collection/add/<int:model_id>', methods=['POST'])
def add_to_collection(model_id):
    if 'user_id' not in session:
        return {'status': 'error', 'message': 'You must be logged in.'}, 401

    collection_id = request.form.get('collection_id')
    if not collection_id:
        return {'status': 'error', 'message': 'No collection selected.'}, 400

    collection_item = CollectionItem.query.filter_by(collection_id=collection_id, model_id=model_id).first()
    if collection_item:
        return {'status': 'error', 'message': 'Model already in this collection.'}, 400

    new_item = CollectionItem(collection_id=collection_id, model_id=model_id)
    db.session.add(new_item)
    db.session.commit()

    return {'status': 'success', 'message': 'Model added to collection.'}


import bleach

@app.route('/comment/add/<int:model_id>', methods=['POST'])
def add_comment(model_id):
    if 'user_id' not in session:
        flash('You must be logged in to comment.')
        return redirect(url_for('login'))

    content = request.form.get('content')
    if content:
        # Sanitize content to prevent XSS
        sanitized_content = bleach.clean(content, tags=[], attributes={}, styles=[], strip=True)
        new_comment = Comment(content=sanitized_content, user_id=session['user_id'], model_id=model_id)
        db.session.add(new_comment)
        db.session.commit()
        flash('Comment added.')

    return redirect(url_for('model_detail', model_id=model_id))


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
