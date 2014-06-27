# import logging

from sqmpy import app

if __name__ == '__main__':
    # logging.basicConfig(filename='sqm.log', level=logging.DEBUG)
    app.run(host='0.0.0.0', port=5001, debug=True)
