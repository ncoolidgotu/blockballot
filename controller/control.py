from flask import Flask, render_template, request


app = Flask(__name__, template_folder='../templates', static_folder='../static')

def query_database(full_name, id, state):
    # Placeholder for database query logic
    return {"full_name": full_name, "id": id, "state": state, "vote": ""}  # Update as necessary

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
        result = query_database(full_name, id, state)
        
        if result and result.get("vote"):
            message = f"Voter status for {full_name}: Vote has been cast for {result['vote']}"
            status = "VOTED"
        elif result:
            message = f"Voter status for {full_name}: Eligible to vote"
            status = "ELIGIBLE"
        else:
            message = "No record found. Please check your details and try again."
        
        print(result, full_name)
    
    return render_template('manage-vote.html', message=message, status=status)

if __name__ == '__main__':
    app.run(debug=True)
