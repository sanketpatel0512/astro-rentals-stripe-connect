import stripe
import os
from flask import Flask, jsonify, request, render_template
from dotenv import load_dotenv
import uuid
import random

load_dotenv()
stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')
app = Flask(__name__)

# ==========================================
# MOCK DATABASE: Simulates your marketplace listings
# ==========================================
MOCK_LISTINGS = {
    "item_001": {
        "name": "ZWO AM5 Harmonic Drive Mount",
        "description": "Weekend Rental. Includes tripod and counterweight.",
        "price_cents": 15000, 
        "owner_account_id": "acct_REPLACE_WITH_YOUR_TEST_ID", # Connect Acc ID placeholder
        "vendor_name": "Astro Rentals Inc.",
        "platform_fee_percent": 0.10 
    },
    "item_002": {
        "name": "Apertura Carbonstar 6\" RC",
        "description": "Deep-sky imaging telescope. Tube only.",
        "price_cents": 8500, 
        "owner_account_id": "acct_REPLACE_WITH_YOUR_TEST_ID", # Connect Acc ID placeholder
        "vendor_name": "Astro Rentals Inc.",
        "platform_fee_percent": 0.10
    }
}

@app.route('/')
def home():
    """Renders the storefront, passing the mock database to the HTML."""
    return render_template('index.html', listings=MOCK_LISTINGS)

@app.route('/success')
def success():
    """Renders the success page after a completed Checkout session."""
    return render_template('success.html')

@app.route('/admin')
def admin_dashboard():
    """Renders the internal Admin Dashboard for platform operations."""
    return render_template('admin.html')

@app.route('/create-checkout-session', methods=['POST'])
def create_checkout_session():
    """
    Dynamically creates a checkout session based on the item requested.
    """
    try:
        data = request.get_json()
        item_id = data.get('item_id')
        item = MOCK_LISTINGS.get(item_id)

        if not item:
            return jsonify(error="Item not found"), 404

        fee_amount = int(item['price_cents'] * item['platform_fee_percent'])

        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'usd',
                    'product_data': {
                        'name': item['name'],
                        'description': item['description']
                    },
                    'unit_amount': item['price_cents'],
                },
                'quantity': 1,
            }],
            mode='payment',
            payment_intent_data={
                'application_fee_amount': fee_amount,
                'transfer_data': {
                    'destination': item['owner_account_id'],
                },
            },
            success_url='http://localhost:4242/success',
            cancel_url='http://localhost:4242/cancel',
        )
        return jsonify({'url': session.url})
    
    except Exception as e:
        print(f"\n--- STRIPE CHECKOUT ERROR --- \n{str(e)}\n--------------------\n")
        return jsonify(error=str(e)), 403

@app.route('/webhook', methods=['POST'])
def webhook():
    """
    Listens for Stripe events to fulfill the rental securely.
    """
    payload = request.data
    sig_header = request.headers.get('Stripe-Signature')
    endpoint_secret = os.environ.get('STRIPE_WEBHOOK_SECRET')

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
    except ValueError:
        return 'Invalid payload', 400
    except stripe.error.SignatureVerificationError:
        return 'Invalid signature', 400

    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        # Generic fulfillment message replacing the hardcoded V1 telescope string
        print(f"Payment successful! Ready to fulfill rental for session: {session['id']}")

    return jsonify(success=True), 200

@app.route('/onboard-vendor', methods=['POST'])
def onboard_vendor():
    """
    Creates a new Connect Express account, dynamically generates a mock 
    equipment listing for them, and returns an onboarding link.
    """
    try:
        account = stripe.Account.create(
            type="express",
            capabilities={
                "card_payments": {"requested": True},
                "transfers": {"requested": True},
            },
            business_type="individual",
        )

        new_item_id = f"item_{str(uuid.uuid4())[:8]}"
        
        mock_gear = random.choice([
            {"name": "ZWO ASI533MC Pro Camera", "desc": "Cooled color astronomy camera.", "price": 6500},
            {"name": "Celestron EdgeHD 8\"", "desc": "Aplanatic Schmidt-Cassegrain.", "price": 12000},
            {"name": "Optolong L-eNhance Filter", "desc": "Dual-band pass filter (2\").", "price": 2500}
        ])

        MOCK_LISTINGS[new_item_id] = {
            "name": mock_gear["name"],
            "description": mock_gear["desc"],
            "price_cents": mock_gear["price"],
            "owner_account_id": account.id,
            "vendor_name": "TheGalacticFrame",
            "platform_fee_percent": 0.10
        }

        account_link = stripe.AccountLink.create(
            account=account.id,
            refresh_url="http://localhost:4242/", 
            return_url="http://localhost:4242/",  
            type="account_onboarding",
        )

        return jsonify({'url': account_link.url})

    except Exception as e:
        print(f"\n--- STRIPE ONBOARD ERROR --- \n{str(e)}\n--------------------\n")
        return jsonify(error=str(e)), 403

@app.route('/delete-vendor', methods=['POST'])
def delete_vendor():
    """
    Deletes a Stripe Connect Account and scrubs their listings from the platform.
    """
    try:
        data = request.get_json()
        account_id = data.get('account_id')

        if not account_id:
            return jsonify(error="Account ID is required"), 400

        deleted_account = stripe.Account.delete(account_id)
        
        keys_to_delete = [k for k, v in MOCK_LISTINGS.items() if v['owner_account_id'] == account_id]
        for k in keys_to_delete:
            del MOCK_LISTINGS[k]
        
        print(f"Successfully deleted vendor account: {deleted_account.id} and their listings.")
        return jsonify({'success': True, 'deleted_id': deleted_account.id})

    except Exception as e:
        print(f"\n--- STRIPE DELETE ERROR --- \n{str(e)}\n--------------------\n")
        return jsonify(error=str(e)), 403

if __name__ == '__main__':
    app.run(port=4242)