from flask import Flask, render_template, request
from model import model


app = Flask(__name__, template_folder='../templates', static_folder='../static')
BLOCKCHAIN = model.Blockchain()

def check_registration_status(full_name, id, state):
    check_for_dupe = BLOCKCHAIN.retrieve_record(full_name, id, state)
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
        
        if status ==  "VOTED":
            message = f"Voter status for {full_name}: Vote has been cast for {result['vote']}"
        elif status == "ELIGIBLE":
            message = f"Voter status for {full_name}: Eligible to vote"
        else:
            message = "No record found. Please check your details and try again."
        
        # print(full_name, id, state)
    
    return render_template('manage-vote.html', message=message, status=status)

@app.route('/cast-vote', methods=['GET', 'POST'])
def cast_vote():
    message = ''
    status = ''

    if request.method == 'POST':
        try:
            full_name = request.form['fullName']
            voter_id = request.form['id']
            state = request.form['state']
            vote = request.form['vote']

            print(full_name, voter_id, state, vote)

            # Process the vote here
            # BLOCKCHAIN.build_block()

            message = 'Vote successfully cast!'
            status = 'SUCCESS'
        except KeyError as e:
            message = f'Missing form field: {e}'
            status = 'ERROR'

    return render_template('cast-vote.html', message=message, status=status, fullName=full_name, id=voter_id, state=state, vote=vote)

@app.route('/status.html', methods=['POST'])
def status_page():
    full_name = request.form['fullName']
    voter_id = request.form['id']
    state = request.form['state']
    
    # Print the information to the console
    print(f"Full Name: {full_name}")
    print(f"Voter ID: {voter_id}")
    print(f"State: {state}")
    
    # Check against the database
    # For the dummy code, simulate database result
    status, result = check_registration_status(full_name, voter_id, state)
    
    if status == "VOTED":
        message = f"Voter status for {full_name}: Vote has been cast for {result['vote']}"
    elif status == "ELIGIBLE":
        message = f"Voter status for {full_name}: Eligible to vote"
    else:
        message = "No record found. Please check your details and try again."
    
    return render_template('status.html', message=message, status=status, fullName=full_name, id=voter_id, state=state, vote=result.get('vote', ''))

@app.route('/secret-vote', methods=['POST'])
def secret_vote():
    full_name = request.form['fullName']
    voter_id = request.form['id']
    state = request.form['state']
    vote = request.form['person']
    if vote == "Independent":
        vote = request.form['IndName']

    print(full_name, voter_id, state, vote)

    # Process the vote here
    # Example: BLOCKCHAIN.build_block()

    message = 'Vote successfully cast!'

    block_to_add = BLOCKCHAIN.build_block(full_name,voter_id,state,vote)
    BLOCKCHAIN.add_block(block_to_add)
    

    return render_template('confirmation.html', message=message)

if __name__ == '__main__':
    app.run(debug=True)