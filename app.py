from flask import Flask, request, abort
import stripe
import psycopg2
from psycopg2 import errors
import os
from dotenv import load_dotenv

if os.environ.get('FLASK_ENV') == 'development':
    from dotenv import load_dotenv
    load_dotenv()  # Load environment variables from .env file in development only

app = Flask(__name__)

stripe.api_key = os.getenv('STRIPE_API_KEY')
endpoint_secret = os.getenv('STRIPE_ENDPOINT_SECRET')

# Endpoint to handle the webhooks
@app.route('/webhook', methods=['POST'])
def stripe_webhook():
    print("Webhook received")
    payload = request.data.decode("utf-8")
    sig_header = request.headers.get('Stripe-Signature')

    # Endpoint's secret from Stripe Dashboard's webhook settings
    endpoint_secret = ''

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
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
    connection_string = "dbname='Augmented_Subscriptions' user='postgres' password='{os.getenv('DB_PASSWORD')}' host='localhost'"
    try:
        with psycopg2.connect(connection_string) as conn:
            with conn.cursor() as cur:
                sql = "INSERT INTO subscribers (customer_id, name, phone, email) VALUES (%s, %s, %s, %s)"
                cur.execute(sql, (customer_id, name, phone, email))
                conn.commit()  # Commit the transaction
    except errors.UniqueViolation as e:
        print("A duplicate phone number error occurred: A customer with this phone number already exists.")
        return False
    except Exception as e:
        print(f"An error occurred: {e}")
        return False
    return True


if __name__ == '__main__':
    app.run(port='4242')  # Port number can be anything you choose
