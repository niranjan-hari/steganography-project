from flask import Flask, request, render_template, send_file
import os

# import your code file (save your original file as stego.py)
import stego

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/')
def home():
    return render_template("project.html")


@app.route('/encode', methods=['POST'])
def encode_route():
    file = request.files['image']
    message = request.form['message']

    input_path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(input_path)

    temp_image = "Niranjan.png"
    output_image = "encoded.png"

    key = stego.generate_key()
    encrypted = stego.encrypt_text(message, key)
    bits = stego.bytes_to_bits(encrypted)

    stego.convert_to_prophoto_16bit(input_path, temp_image)
    stego.embed_data(temp_image, output_image, bits)

    return f"""
    <h2>Encoded Successfully</h2>
    <p>Key: {key.decode()}</p>
    <p>Bit Length: {len(bits)}</p>
    <a href="/download">Download Image</a>
    """


@app.route('/download')
def download():
    return send_file("encoded.png", as_attachment=True)


@app.route('/decode', methods=['POST'])
def decode_route():
    file = request.files['image']
    key = request.form['key'].encode()
    bit_length = int(request.form['bit_length'])

    input_path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(input_path)

    bits = stego.extract_data(input_path, bit_length)
    data = stego.bits_to_bytes(bits)
    message = stego.decrypt_text(data, key)

    return f"<h2>Message:</h2><p>{message}</p>"


import os

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
