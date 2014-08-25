from sqmpy import app

if __name__ == '__main__':
    """
    Run application directly. Some samples:
        app.run(host='localhost', port=5001)
        # port will be read from SERVER_NAME or will be 5000
        app.run(host='localhost')
        # host will be 127.0.0.1
        # port will be read from SERVER_NAME or will be 5000
        app.run()

        # Pleae note that SERVER_NAME is used for subdomains only and has no effect here.
    """
    app.run(host='localhost')
