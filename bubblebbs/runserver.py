import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from bubblebbs import app


app.app.debug = True
app.app.run(host='0.0.0.0', port=8080, debug=True)
