from controller.control import app

def run_app():
    app.run(host='0.0.0.0', port=5000)

if __name__ == '__main__':
    run_app()