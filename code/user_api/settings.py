import os


API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:5000").rstrip("/")
REPORT_IMAGES_DIR = os.getenv("REPORT_IMAGES_DIR", "/mnt/report-images")
UPLOAD_IMAGE_SIZE_LIMIT = 8 * 1024 * 1024
ALLOWED_IMAGE_EXTENSIONS = [".jpg", ".png", ".jpeg"]
