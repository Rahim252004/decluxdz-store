import os
import uuid
from flask import current_app
from werkzeug.utils import secure_filename

# All 58 Algerian provinces
ALGERIAN_PROVINCES = [
    "أدرار", "الشلف", "الأغواط", "أم البواقي", "باتنة", "بجاية", "بسكرة", "بشار",
    "البليدة", "البويرة", "تمنراست", "تبسة", "تلمسان", "تيارت", "تيزي وزو", "الجزائر",
    "الجلفة", "جيجل", "سطيف", "سعيدة", "سكيكدة", "سيدي بلعباس", "عنابة", "قالمة",
    "قسنطينة", "المدية", "مستغانم", "المسيلة", "معسكر", "ورقلة", "وهران", "البيض",
    "إليزي", "برج بوعريريج", "بومرداس", "الطارف", "تندوف", "تيسمسيلت", "الوادي",
    "خنشلة", "سوق أهراس", "تيبازة", "ميلة", "عين الدفلى", "النعامة", "عين تموشنت",
    "غرداية", "غليزان", "تيميمون", "برج باجي مختار", "أولاد جلال", "بني عباس",
    "إن صالح", "إن قزام", "توقرت", "جانت", "المغير", "المنيعة"
]



ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_uploaded_file(file, folder=None):
    if file and allowed_file(file.filename):
        # نحدد المجلد: إذا ما عطيناش واحد، نستخدم UPLOAD_FOLDER من إعدادات Flask
        upload_folder = folder or current_app.config['UPLOAD_FOLDER']

        # نولّي نتأكد أن المجلد موجود
        os.makedirs(upload_folder, exist_ok=True)

        # نولّد اسم ملف فريد
        filename = secure_filename(file.filename)
        name, ext = os.path.splitext(filename)
        unique_filename = f"{name}_{uuid.uuid4().hex[:8]}{ext}"

        # المسار النهائي
        file_path = os.path.join(upload_folder, unique_filename)
        file.save(file_path)

        return unique_filename  # نخزن الاسم فقط في قاعدة البيانات
    return None
def generate_order_number():
    """Generate a unique order number"""
    import random
    import string
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
