
from webopeneoct import app
# Run application on the given setting.
app.run(host="0.0.0.0", port="5000", debug=True, threaded=True, ssl_context=('cert.pem', 'key.pem'))
