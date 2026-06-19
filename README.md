# Astro Rentals: Stripe Connect Marketplace Architecture

## Overview
This project demonstrates a fully functional peer-to-peer marketplace backend using **Stripe Connect** and **Stripe Checkout**. It models a platform ("Astro Rentals") where users can rent specialized astrophotography equipment from independent vendors.

This architecture handles complex money movement by securely accepting payments, retaining a platform application fee, and automatically routing the remaining funds to the appropriate vendor's Connected Account using Destination Charges.

## Technical Stack
* **Backend:** Python / Flask
* **Frontend:** HTML / Vanilla JavaScript (Jinja2 Templating)
* **Stripe APIs Used:** * `stripe.checkout.Session` (Payment Processing & Routing)
  * `stripe.Webhook` (Secure Fulfillment)
  * `stripe.Account` & `stripe.AccountLink` (Connect Express Onboarding)
  * `stripe.Account.delete` (Compliance & Data Offboarding)

## Business Value & Solution Strategy
1. **Frictionless Onboarding:** Utilizes Stripe-hosted Connect Onboarding flows via `AccountLink` to allow vendors to sign up. This abstracts the immense compliance, KYC (Know Your Customer), and identity verification burdens away from the platform.
2. **Automated Revenue Splits:** Employs Destination Charges within the `payment_intent_data` to automatically split transactions. The platform retains a dynamic percentage (e.g., 10%) as an application fee, while the remainder is seamlessly routed to the vendor's Stripe account.
3. **PCI Compliance:** Leverages Stripe Checkout to ensure the platform backend never touches sensitive raw credit card data, drastically reducing the platform's PCI compliance scope.
4. **Lifecycle Management:** Includes a dedicated admin portal to manage vendor offboarding and data compliance, simulating real-world Enterprise platform operations.

## Project Structure
```text
/
├── .env                    # Environment variables template
├── AstroRentalApp.py       # Main Flask application and Stripe API logic
└── templates/              
    ├── index.html          # Dynamic marketplace storefront
    ├── success.html        # Post-checkout success landing page
    └── admin.html          # Internal tool for vendor offboarding