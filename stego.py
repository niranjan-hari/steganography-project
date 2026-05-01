import os
from cryptography.fernet import Fernet
from PIL import Image, ImageCms
import numpy as np
import imageio.v3 as iio
import cv2

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ICC_PATH = os.path.join(BASE_DIR, "ProPhoto.icc")

# =========================
# 🔐 ENCRYPTION
# =========================
def generate_key():
    return Fernet.generate_key()

def encrypt_text(text, key):
    return Fernet(key).encrypt(text.encode())

def decrypt_text(data, key):
    return Fernet(key).decrypt(data).decode()

# =========================
# 🔁 BIT CONVERSION
# =========================
def bytes_to_bits(data):
    return ''.join(format(b, '08b') for b in data)

def bits_to_bytes(bits):
    return bytes(int(bits[i:i+8], 2) for i in range(0, len(bits), 8))

# =========================
# 💾 16-bit PNG I/O (OpenCV)
# =========================
def save_16bit_png(path, arr_rgb_uint16):
    # OpenCV expects BGR
    bgr = arr_rgb_uint16[:, :, ::-1]
    ok = cv2.imwrite(path, bgr)
    if not ok:
        raise RuntimeError("Failed to write 16-bit PNG with OpenCV")

def load_16bit_png(path):
    # Load as-is (preserves uint16)
    bgr = cv2.imread(path, cv2.IMREAD_UNCHANGED)
    if bgr is None:
        raise RuntimeError("Failed to read image")
    if bgr.dtype != np.uint16 or bgr.ndim != 3 or bgr.shape[2] != 3:
        raise ValueError("Image must be 16-bit RGB (uint16, 3 channels)")
    rgb = bgr[:, :, ::-1]
    return rgb

# =========================
# 🎨 PROPHOTO + 16-BIT RGB
# =========================
def convert_to_prophoto_16bit(input_path, output_path):
    img = Image.open(input_path).convert("RGB")

    # Build transform sRGB -> ProPhoto
    srgb = ImageCms.createProfile("sRGB")
    prophoto = ImageCms.getOpenProfile(ICC_PATH)
    transform = ImageCms.buildTransformFromOpenProfiles(
        srgb, prophoto, "RGB", "RGB"
    )

    img = ImageCms.applyTransform(img, transform)

    # 8-bit RGB -> numpy
    arr8 = np.array(img, dtype=np.uint8)

    # Scale to 16-bit RGB (0..255 -> 0..65535)
    arr16 = (arr8.astype(np.uint16) << 8)

    # Write with OpenCV (supports 16-bit RGB PNG)
    save_16bit_png(output_path, arr16)

# =========================
# 🧬 EMBED DATA (2 LSBs / channel)
# =========================
def embed_data(image_path, output_path, bits):
    img = load_16bit_png(image_path)  # uint16, (H,W,3)

    flat = img.reshape(-1)

    capacity = len(flat) * 2  # 2 bits per element
    if len(bits) > capacity:
        raise ValueError(f"Message too large: need {len(bits)} bits, have {capacity}")

    bit_idx = 0
    for i in range(len(flat)):
        if bit_idx >= len(bits):
            break

        # clear last 2 bits
        flat[i] &= np.uint16(0xFFFC)

        # pack next 2 bits
        val = 0
        for _ in range(2):
            if bit_idx < len(bits):
                val = (val << 1) | int(bits[bit_idx])
                bit_idx += 1
            else:
                val <<= 1

        flat[i] |= val

    out = flat.reshape(img.shape)
    save_16bit_png(output_path, out)

# =========================
# 🔍 EXTRACT DATA
# =========================
def extract_data(image_path, bit_length):
    img = load_16bit_png(image_path)
    flat = img.reshape(-1)

    bits = []
    count = 0

    for val in flat:
        # extract 2 LSBs (MSB-first within the pair)
        for shift in (1, 0):
            if count >= bit_length:
                break
            bits.append(str((val >> shift) & 1))
            count += 1
        if count >= bit_length:
            break

    return ''.join(bits)

# =========================
# 🚀 ENCODE PIPELINE
# =========================
def encode():
    input_image = input("Enter path to your image: ").strip()

    temp_image = "temp_prophoto_16bit.png"
    output_image = "encoded.png"

    message = input("Enter message to hide: ")

    key = generate_key()
    print(f"\n🔑 SAVE THIS KEY: {key.decode()}\n")

    encrypted = encrypt_text(message, key)
    bits = bytes_to_bits(encrypted)

    print("⚙️ Converting to ProPhoto RGB + 16-bit...")
    convert_to_prophoto_16bit(input_image, temp_image)

    print("🔐 Embedding data...")
    embed_data(temp_image, output_image, bits)

    print(f"✅ Done! Saved as {output_image}")
    print(f"📏 Bit length (needed for decode): {len(bits)}")

# =========================
# 🔓 DECODE PIPELINE
# =========================
def decode():
    encoded_image = input("Enter encoded image path: ").strip()
    key = input("Enter key: ").encode()
    bit_length = int(input("Enter bit length: "))

    bits = extract_data(encoded_image, bit_length)
    data = bits_to_bytes(bits)

    message = decrypt_text(data, key)
    print("\n📨 Recovered message:")
    print(message)

# =========================
# 🎯 MAIN
# =========================
if __name__ == "__main__":
    mode = input("Choose mode (encode/decode): ").strip().lower()

    if mode == "encode":
        encode()
    elif mode == "decode":
        decode()
    else:
        print("Invalid mode")
#C:/Users/Niranjan H/Downloads/rf/Niranjan.png
#vIfm2urrT_rDvQxubuhi7bjhWdrd73foV2-D4rGOcoo=
