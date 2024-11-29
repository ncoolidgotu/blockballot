from flask import Flask, render_template, request, send_file
import io
from model import model
import html
from datetime import datetime

app = Flask(__name__, template_folder='../templates', static_folder='../static')
BLOCKCHAIN = model.Blockchain()

def check_registration_status(full_name, id, state):
    '''
    Connects to back end that returns a tuple
    1st element: True if the user has already voted, False if they havent
    2nd element: dictionary with voter info - empty if they havent voted

    this function returns the following tuple
    1st element: str of "VOTED" or "ELIGIBLE"
    2nd element: a dictionary with voter info
    '''
    check_for_dupe = BLOCKCHAIN.retrieve_record(full_name, id, state)
    if check_for_dupe[0] == True:
        status = "VOTED"
        return status, check_for_dupe[1]
    elif check_for_dupe[0] == False:
        status = "ELIGIBLE"
        return status, check_for_dupe[1]


# Different HTTP Error Handler Routes
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(e):
    return render_template('500.html'), 500

@app.errorhandler(405)
def method_not_allowed(e):
    return render_template('405.html'), 405

# Home page
@app.route('/')
def index():
    votes, vote_state_data = BLOCKCHAIN.tally_votes()
    return render_template('index.html', votes=votes, vote_state_data=vote_state_data)

# "VOTE!!" on NavBar - user puts information to get voting status
@app.route('/manage-vote', methods=['GET'])
def manage_vote():
    return render_template('manage-vote.html')

# Returns vote eligibility. If the user has already voted, their casted vote is returned instead.
@app.route('/status.html', methods=['POST'])
def status_page():
    full_name = request.form['fullName']
    voter_id = request.form['id']
    state = request.form['state']

    # Check against the database, and change the status
    # Status can be "ELIGIBLE" or "VOTED"
    status, result = check_registration_status(full_name, voter_id, state)
    
    # Return information accordingly
    if status == "VOTED":
        message = f"Voter status for {full_name}: Vote has been cast for {result['vote']}"
    elif status == "ELIGIBLE":
        message = f"Voter status for {full_name}: Eligible to vote"
    else:
        message = "Your information couldn't be verified. Please check your details and try again. \n Alternatively try contacting your local government"
    
    return render_template('status.html', message=message, status=status, fullName=full_name, id=voter_id, state=state, vote=result.get('vote', ''))

# If in status the user was eligible to vote, they can vote from this redirected page
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

            status = 'SUCCESS'
        except KeyError as e:
            message = f'Missing form field: {e}'
            status = 'ERROR'

    return render_template('cast-vote.html', message=message, status=status, fullName=full_name, id=voter_id, state=state, vote=vote)

# Having voted, this returns a confirmation message, as well as the hash and key to verify the vote later on
@app.route('/confirmation-vote', methods=['POST'])
def confirmation_vote():
    full_name = request.form['fullName']
    voter_id = request.form['id']
    state = request.form['state']
    vote = request.form['person']
    if vote == "Independent":
        vote = request.form['IndName']

    try:
        # The block is mined and added to the blockchain
        block_to_add = BLOCKCHAIN.build_block(full_name,voter_id,state,vote)
        if block_to_add != {}:
            public_key = BLOCKCHAIN.add_block(block_to_add)
            hash_of_voter = BLOCKCHAIN.get_voter_hash(full_name, voter_id, state)
            
            print("HERE:",public_key)
            
            message = (
                'Vote successfully cast!\n'
                'You can verify your vote using the following PUBLIC KEY and HASH:\n'
                'ENSURE YOU SAVE IT AS YOU WILL NOT SEE IT AGAIN!!!'
            )

        else:
            'There was an error casting your vote! The blockchain may have been compromised!'

    except:
        message = 'There was an error casting your vote! Please try again later or contact our support team'
    
    return render_template('confirmation.html', message=message,public_key=public_key, hash_of_voter=hash_of_voter, full_name=full_name)

# To view the entire blockchain
@app.route('/view-ledger', methods=['GET'])
def view_ledger():
    data = BLOCKCHAIN.validate_blockchain()
    return render_template('view-ledger.html', data=data)

# to verify one's own vote a hash and a public key
@app.route('/verify-vote', methods=['GET', 'POST'])
def verify_vote():
    if request.method == 'POST':
        # Check if the user has uploaded both files
        user_hash_file = request.files.get('user_hash')
        public_key_file = request.files.get('public_key')
        
        if user_hash_file and public_key_file:
            # Read the contents of the files (assuming they're text files)
            user_hash = user_hash_file.read().decode('utf-8')  # Decoding from bytes to string
            pk_bytes = public_key_file.read()
            public_key = html.unescape(pk_bytes.decode('utf-8')).strip()  # Decoding from bytes to string
            public_key = public_key[2:-1]
            
            print(public_key)
            
            # For example, print the contents to the console
            print("User Hash:", user_hash)
            print("Public Key:", public_key)
            
            block, message = BLOCKCHAIN.verify_vote(public_key, user_hash)

            # Pass the data to a template or process further
            return render_template('verify-vote.html', message=message, block=block)
        else:
            return "Error: Both files are required!", 400

    return render_template('verify-vote.html')

# Different routes to be returned for the different error handlers mentioned previously (top of code)
@app.route('/404')
def not_found_page():
    return render_template('404.html')

@app.route('/500')
def internal_error_page():
    return render_template('500.html')

@app.route('/405')
def method_not_allowed_page():
    return render_template('405.html')

# Custom filter to convert epoch timestamp to human-readable format
@app.template_filter('epoch_to_datetime')
def epoch_to_datetime(epoch):
    return datetime.utcfromtimestamp(epoch).strftime('%Y-%m-%d %H:%M:%S')

if __name__ == '__main__':
    app.run(debug=True)