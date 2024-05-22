from flask import Flask, request, abort
import stripe
import psycopg2
from psycopg2 import errors
import os   
from dotenv import load_dotenv
from flask_sqlalchemy import SQLAlchemy


if os.environ.get('FLASK_ENV') == 'development':
    from dotenv import load_dotenv
    load_dotenv()  # Load environment variables from .env file in development only

app = Flask(__name__)


#STRIPE API KEYS
stripe.api_key = os.getenv('STRIPE_API_KEY')
endpoint_secret = os.getenv('STRIPE_ENDPOINT_SECRET')


# Configure SQLAlchemy with DATABASE_URL
database_url = os.getenv('DATABASE_URL')
if database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)  # Fix for SQLAlchemy compatibility

app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Model definition
class Subscriber(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.String(255), unique=True, nullable=False)
    name = db.Column(db.String(255), nullable=False)
    phone = db.Column(db.String(50), nullable=True)
    email = db.Column(db.String(255), nullable=True)


# Endpoint to handle the webhooks
@app.route('/webhook', methods=['POST'])
def stripe_webhook():
    print("Webhook received")
    payload = request.data.decode("utf-8")
    print("Webhook received with payload:", payload)  # This can be quite verbose if payloads are large
    sig_header = request.headers.get('Stripe-Signature')

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
    except stripe.error.SignatureVerificationError as e:
        print("Invalid signature")
        abort(400)
    except ValueError as e:
        # Invalid payload
        print("Invalid payload")
        abort(400)
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        print("Invalid signature")
        abort(400)

    # Handle the event
    if event['type'] == 'customer.created':
        customer = event['data']['object']
        customer_id = customer['id']
        name = customer.get('name')
        phone = customer.get('phone')
        email = customer.get('email')
        
        # Call function to save data to PostgreSQL
        save_customer_to_db(customer_id, name, phone, email)

    return 'Received!', 200

def save_customer_to_db(customer_id, name, phone, email):
    try:
        new_subscriber = Subscriber(customer_id=customer_id, name=name, phone=phone, email=email)
        db.session.add(new_subscriber)
        db.session.commit()
        print("Subscriber added successfully.")
        return True
    except Exception as e:
        db.session.rollback()  # Roll back the transaction on error
        print(f"An error occurred: {e}")
        return False


if __name__ == '__main__':
    app.run()  # Port number can be anything you choose
