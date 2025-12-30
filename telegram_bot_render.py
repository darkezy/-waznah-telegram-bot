# تم إضافة:
from threading import Thread
from http.server import HTTPServer, BaseHTTPRequestHandler

# HTTP Server بسيط
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(b"Bot is running!")

def run_http_server():
    PORT = int(os.environ.get('PORT', 10000))
    server = HTTPServer(('0.0.0.0', PORT), HealthCheckHandler)
    server.serve_forever()

# في main():
http_thread = Thread(target=run_http_server, daemon=True)
http_thread.start()
