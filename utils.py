import random
import string

def generate_short_code(length=6):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

def get_client_ip(request):
    return request.headers.get('X-Forwarded-For', request.remote_addr)
