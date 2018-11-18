import sys
import os

from flask_socketio import SocketIO

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from bubblebbs import app


app, socketio = app.create_app()
socketio = SocketIO(app)
app.debug = True
#app.run(host='0.0.0.0', port=8080, debug=True)
socketio.run(app, host='0.0.0.0', port=8080, debug=True)
