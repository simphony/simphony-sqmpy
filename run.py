from sqmpy import app

if __name__ == '__main__':
    #import logging
    #logging.basicConfig(filename='sqmpy.log', level=logging.DEBUG)
    #app = init_app()

    app.run(host='0.0.0.0', port=5001, debug=True)
