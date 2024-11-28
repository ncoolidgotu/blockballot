from flask import Flask, render_template, request
from model import model


app = Flask(__name__, template_folder='../templates', static_folder='../static')
BLOCKCHAIN = model.Blockchain()

def check_registration_status(full_name, id, state):
    check_for_dupe = BLOCKCHAIN.retrieve_record(full_name, id, state)
    print(check_for_dupe)
    if check_for_dupe[0] == True:
        status = "VOTED"
        return status, check_for_dupe[1]
    elif check_for_dupe[0] == False:
        status = "ELIGIBLE"
        return status, check_for_dupe[1]

@app.route('/')
def index():
    return render_template('index.html')
from flask import Flask, render_template, request

@app.route('/manage-vote', methods=['GET', 'POST'])
def manage_vote():
    message = ''
    status = ''
    if request.method == 'POST':
        full_name = request.form['fullName']
        id = request.form['id']
        state = request.form['state']
        
        # Check against the database
        # For the dummy code, simulate database result
        status, result = check_registration_status(full_name, id, state)
        print(status)
        
        if status ==  "VOTED":
            message = f"Voter status for {full_name}: Vote has been cast for {result['vote']}"
        elif status == "ELIGIBLE":
            message = f"Voter status for {full_name}: Eligible to vote"
        else:
            message = "No record found. Please check your details and try again."
        
        print(full_name, id, state)
    
    return render_template('manage-vote.html', message=message, status=status)

if __name__ == '__main__':
    app.run(debug=True)
