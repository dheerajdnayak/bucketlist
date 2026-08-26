from flask import Flask, render_template, redirect, url_for, flash, request, jsonify, send_from_directory
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from models import db, User, BucketItem
from forms import SignupForm, LoginForm
import os
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-change-in-production'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///bucketlist.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Upload folder for images
UPLOAD_FOLDER = os.path.join(app.static_folder, 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB

db.init_app(app)

login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access your bucketlist.'
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ---------- Routes ----------
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    form = SignupForm()
    if form.validate_on_submit():
        existing = User.query.filter((User.username == form.username.data) | (User.email == form.email.data)).first()
        if existing:
            flash('Username or email already exists.', 'danger')
            return redirect(url_for('signup'))
        hashed = generate_password_hash(form.password.data)
        user = User(username=form.username.data, email=form.email.data, password_hash=hashed)
        db.session.add(user)
        db.session.commit()
        flash('Account created! Please log in.', 'success')
        return redirect(url_for('login'))
    return render_template('signup.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and check_password_hash(user.password_hash, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('dashboard'))
        flash('Invalid username or password.', 'danger')
    return render_template('login.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

# ---------- Dashboard ----------
@app.route('/dashboard')
@login_required
def dashboard():
    items = BucketItem.query.filter_by(user_id=current_user.id).order_by(BucketItem.updated_at.desc()).all()
    return render_template('dashboard.html', items=items)

# ---------- Create new item ----------
@app.route('/item/new')
@login_required
def new_item():
    item = BucketItem(title='Untitled', content='', user_id=current_user.id)
    db.session.add(item)
    db.session.commit()
    return redirect(url_for('edit_item', item_id=item.id))

# ---------- Edit item (full-page editor) ----------
@app.route('/item/<int:item_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_item(item_id):
    item = BucketItem.query.get_or_404(item_id)
    if item.user_id != current_user.id:
        flash('Permission denied.', 'danger')
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        content = request.form.get('content', '')
        if not title:
            flash('Title is required.', 'danger')
        else:
            item.title = title
            item.content = content
            item.updated_at = datetime.utcnow()
            db.session.commit()
            flash('Item saved.', 'success')
        return redirect(url_for('edit_item', item_id=item.id))
    
    return render_template('item_edit.html', item=item)

# ---------- Delete item ----------
@app.route('/item/<int:item_id>/delete')
@login_required
def delete_item(item_id):
    item = BucketItem.query.get_or_404(item_id)
    if item.user_id != current_user.id:
        flash('Permission denied.', 'danger')
        return redirect(url_for('dashboard'))
    db.session.delete(item)
    db.session.commit()
    flash('Item deleted.', 'info')
    return redirect(url_for('dashboard'))

# ---------- Toggle completion ----------
@app.route('/item/<int:item_id>/complete')
@login_required
def complete_item(item_id):
    item = BucketItem.query.get_or_404(item_id)
    if item.user_id != current_user.id:
        flash('Permission denied.', 'danger')
        return redirect(url_for('dashboard'))
    item.is_completed = not item.is_completed
    db.session.commit()
    flash('Status updated.', 'success')
    return redirect(url_for('dashboard'))

# ---------- Image upload for CKEditor ----------
@app.route('/upload', methods=['POST'])
@login_required
def upload_image():
    if 'upload' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    file = request.files['upload']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    filename = secure_filename(file.filename)
    # Add timestamp to avoid collisions
    name, ext = os.path.splitext(filename)
    filename = f"{name}_{int(datetime.utcnow().timestamp())}{ext}"
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)
    # Return the URL to the image
    url = url_for('static', filename=f'uploads/{filename}')
    return jsonify({'url': url})

# (Optional) Serve uploaded files directly (already served by static)
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, host="0.0.0.0")