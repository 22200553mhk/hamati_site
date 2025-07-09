import sys, os

# اضافه کردن مسیر پروژه به مسیرهای جستجوی پایتون
sys.path.insert(0, os.path.dirname(__file__))

# تنظیم متغیر محیطی Django
os.environ['DJANGO_SETTINGS_MODULE'] = 'konkur.settings'  # نام پروژه را تغییر دهید

# تست دسترسی به Django
try:
    from django.core.wsgi import get_wsgi_application
    application = get_wsgi_application()
except Exception as e:
    # ایجاد یک اپلیکیشن ساده اگر Django کار نکرد
    error_msg = str(e)
    def application(environ, start_response):
        status = '200 OK'
        output = f"Django error: {error_msg}".encode('utf-8')
        response_headers = [('Content-type', 'text/plain'),
                          ('Content-Length', str(len(output)))]
        start_response(status, response_headers)
        return [output]