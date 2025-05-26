import os
from werkzeug.utils import secure_filename
from datetime import datetime

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_file(file, app):
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_')
        unique_filename = timestamp + filename
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], unique_filename))
        return f'/static/uploads/{unique_filename}'
    return None

def delete_file(filepath, app):
    if filepath:
        try:
            full_path = os.path.join(app.root_path, filepath.lstrip('/'))
            if os.path.exists(full_path):
                os.remove(full_path)
                return True
        except Exception as e:
            print(f"Error deleting file: {e}")
    return False