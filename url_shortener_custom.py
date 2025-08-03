from flask import Flask, request, redirect, jsonify, render_template_string
from urllib.parse import urlparse
import string
import random
import sqlite3
import re

app = Flask(__name__)

# Inisialisasi database
def init_db():
    conn = sqlite3.connect('urls.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS urls 
                (short_code TEXT PRIMARY KEY, original_url TEXT)''')
    conn.commit()
    conn.close()

# Generate kode pendek acak
def generate_short_code(length=6):
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(length))

# Validasi kode kustom
def is_valid_custom_code(code):
    return bool(re.match(r'^[a-zA-Z0-9_-]{3,10}$', code))  # Hanya huruf, angka, _, -, panjang 3-10

# Cek apakah kode sudah ada di database
def code_exists(short_code):
    conn = sqlite3.connect('urls.db')
    c = conn.cursor()
    c.execute("SELECT 1 FROM urls WHERE short_code = ?", (short_code,))
    exists = c.fetchone() is not None
    conn.close()
    return exists

# Simpan URL ke database
def store_url(original_url, short_code):
    conn = sqlite3.connect('urls.db')
    c = conn.cursor()
    c.execute("INSERT INTO urls (short_code, original_url) VALUES (?, ?)", 
             (short_code, original_url))
    conn.commit()
    conn.close()

# Ambil URL asli dari kode pendek
def get_original_url(short_code):
    conn = sqlite3.connect('urls.db')
    c = conn.cursor()
    c.execute("SELECT original_url FROM urls WHERE short_code = ?", (short_code,))
    result = c.fetchone()
    conn.close()
    return result[0] if result else None

# Route untuk halaman utama
@app.route('/')
def index():
    return render_template_string('''
    <html>
        <body>
            <h2>Pemendek URL</h2>
            <form action="/shorten" method="post">
                <input type="url" name="url" placeholder="Masukkan URL" required>
                <input type="text" name="custom_code" placeholder="Kode kustom (opsional, 3-10 karakter)">
                <input type="submit" value="Pendekkan">
            </form>
            {% if short_url %}
                <p>URL Pendek: <a href="{{ short_url }}">{{ short_url }}</a></p>
            {% endif %}
            {% if error %}
                <p style="color: red;">Error: {{ error }}</p>
            {% endif %}
        </body>
    </html>
    ''')

# Route untuk memendekkan URL
@app.route('/shorten', methods=['POST'])
def shorten_url():
    original_url = request.form['url']
    custom_code = request.form.get('custom_code', '').strip()

    # Validasi URL
    if not original_url.startswith(('http://', 'https://')):
        original_url = 'http://' + original_url

    # Tentukan kode pendek
    if custom_code:
        if not is_valid_custom_code(custom_code):
            return render_template_string('''
                <html>
                    <body>
                        <h2>Pemendek URL</h2>
                        <form action="/shorten" method="post">
                            <input type="url" name="url" placeholder="Masukkan URL" required>
                            <input type="text" name="custom_code" placeholder="Kode kustom (opsional, 3-10 karakter)">
                            <input type="submit" value="Pendekkan">
                        </form>
                        <p style="color: red;">Kode kustom tidak valid! Gunakan 3-10 karakter (huruf, angka, _, -).</p>
                    </body>
                </html>
            ''')
        if code_exists(custom_code):
            return render_template_string('''
                <html>
                    <body>
                        <h2>Pemendek URL</h2>
                        <form action="/shorten" method="post">
                            <input type="url" name="url" placeholder="Masukkan URL" required>
                            <input type="text" name="custom_code " placeholder="Kode kustom (opsional, 3-10 karakter)">
                            <input type="submit" value="Pendekkan">
                        </form>
                        <p style="color: red;">Kode kustom sudah digunakan! Coba kode lain.</p>
                    </body>
                </html>
            ''')
        short_code = custom_code
    else:
        # Generate kode acak jika tidak ada kode kustom
        while True:
            short_code = generate_short_code()
            if not code_exists(short_code):
                break

    # Simpan ke database
    store_url(original_url, short_code)

    # Buat URL pendek
    domain = urlparse(request.base_url).netloc
    short_url = f"http://{domain}/{short_code}"

    return render_template_string('''
        <html>
            <body>
                <h2>Pemendek URL</h2>
                <form action="/shorten" method="post">
                    <input type="url" name="url" placeholder="Masukkan URL" required>
                    <input type="text" name="custom_code" placeholder="Kode kustom (opsional, 3-10 karakter)">
                    <input type="submit" value="Pendekkan">
                </form>
                <p>URL Pendek: <a href="{{ short_url }}">{{ short_url }}</a></p>
            </body>
        </html>
    ''', short_url=short_url)

# Route untuk redirect
@app.route('/<short_code>')
def redirect_url(short_code):
    original_url = get_original_url(short_code)
    if original_url:
        return redirect(original_url)
    return 'URL tidak ditemukan', 404

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
