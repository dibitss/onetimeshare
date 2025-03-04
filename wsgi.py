"""WSGI entry point for OneTimeShare."""
import os
from onetimeshare import create_app

app = create_app('development')

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=True) 