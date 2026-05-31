import os

HOSTNAME = "http://0.0.0.0:5000"
REPORT_IMAGES_DIR = os.getenv("REPORT_IMAGES_DIR", "/mnt/report-images")
UPLOAD_IMAGE_SIZE_LIMIT = 8 * 1024 * 1024
ALLOWED_IMAGE_EXTENSIONS = [".jpg", ".png", ".jpeg"]
