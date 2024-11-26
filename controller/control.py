from flask import Flask, render_template, request


app = Flask(__name__, template_folder='../templates', static_folder='../static')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/check-status', methods=['GET', 'POST'])
def check_status():
    message = ''
    if request.method == 'POST':
        full_name = request.form['fullName']
        id = request.form['id']
        state = request.form['state']
        
        # Check against the database
        
        #result = query_database(full_name, id, state)
        result = None
        
        if result:
            message = f"Voter status for {full_name}: Verified"
        else:
            message = "No record found. Please check your details and try again."
        
        print(result, full_name)
    
    return render_template('check-status.html', message=message)