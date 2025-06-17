import requests
import base64
from datetime import datetime
import os
import logging
import hashlib
import hmac

class MpesaAPI:
    def __init__(self):
        self.consumer_key = os.getenv('MPESA_CONSUMER_KEY', '')
        self.consumer_secret = os.getenv('MPESA_CONSUMER_SECRET', '')
        self.shortcode = os.getenv('MPESA_SHORTCODE', '')
        self.passkey = os.getenv('MPESA_PASSKEY', '')
        self.environment = os.getenv('MPESA_ENVIRONMENT', 'sandbox')  # sandbox or production
        
        # Till numbers for different shops and licensing
        self.license_till = '0797237383'  # Super admin phone for licensing
        
        if self.environment == 'production':
            self.base_url = 'https://api.safaricom.co.ke'
        else:
            self.base_url = 'https://sandbox.safaricom.co.ke'
    
    def get_access_token(self):
        """Get access token for MPesa API"""
        try:
            auth_url = f"{self.base_url}/oauth/v1/generate?grant_type=client_credentials"
            
            # Encode credentials
            credentials = base64.b64encode(
                f"{self.consumer_key}:{self.consumer_secret}".encode()
            ).decode()
            
            headers = {
                'Authorization': f'Basic {credentials}',
                'Content-Type': 'application/json'
            }
            
            response = requests.get(auth_url, headers=headers)
            response.raise_for_status()
            
            return response.json().get('access_token')
            
        except Exception as e:
            logging.error(f"Failed to get MPesa access token: {e}")
            return None
    
    def register_c2b_urls(self, till_number, confirmation_url, validation_url):
        """Register C2B confirmation and validation URLs for a specific till"""
        try:
            access_token = self.get_access_token()
            if not access_token:
                return False
            
            url = f"{self.base_url}/mpesa/c2b/v1/registerurl"
            
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                "ShortCode": till_number,
                "ResponseType": "Completed",
                "ConfirmationURL": confirmation_url,
                "ValidationURL": validation_url
            }
            
            response = requests.post(url, json=payload, headers=headers)
            response.raise_for_status()
            
            result = response.json()
            logging.info(f"C2B URL registration response for {till_number}: {result}")
            
            return result.get('ResponseCode') == '0'
            
        except Exception as e:
            logging.error(f"Failed to register C2B URLs for {till_number}: {e}")
            return False
    
    def simulate_c2b_payment(self, amount, msisdn, bill_ref_number):
        """Simulate C2B payment (for testing in sandbox)"""
        try:
            access_token = self.get_access_token()
            if not access_token:
                return False
            
            url = f"{self.base_url}/mpesa/c2b/v1/simulate"
            
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                "ShortCode": self.shortcode,
                "CommandID": "CustomerPayBillOnline",
                "Amount": amount,
                "Msisdn": msisdn,
                "BillRefNumber": bill_ref_number
            }
            
            response = requests.post(url, json=payload, headers=headers)
            response.raise_for_status()
            
            result = response.json()
            logging.info(f"C2B simulation response: {result}")
            
            return result.get('ResponseCode') == '0'
            
        except Exception as e:
            logging.error(f"Failed to simulate C2B payment: {e}")
            return False
    
    def generate_password(self):
        """Generate password for STK Push"""
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        password_string = f"{self.shortcode}{self.passkey}{timestamp}"
        password = base64.b64encode(password_string.encode()).decode()
        return password, timestamp
    
    def stk_push(self, phone_number, amount, account_reference, transaction_desc, callback_url):
        """Initiate STK Push payment"""
        try:
            access_token = self.get_access_token()
            if not access_token:
                return None
            
            url = f"{self.base_url}/mpesa/stkpush/v1/processrequest"
            
            password, timestamp = self.generate_password()
            
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                "BusinessShortCode": self.shortcode,
                "Password": password,
                "Timestamp": timestamp,
                "TransactionType": "CustomerPayBillOnline",
                "Amount": amount,
                "PartyA": phone_number,
                "PartyB": self.shortcode,
                "PhoneNumber": phone_number,
                "CallBackURL": callback_url,
                "AccountReference": account_reference,
                "TransactionDesc": transaction_desc
            }
            
            response = requests.post(url, json=payload, headers=headers)
            response.raise_for_status()
            
            result = response.json()
            logging.info(f"STK Push response: {result}")
            
            return result
            
        except Exception as e:
            logging.error(f"STK Push failed: {e}")
            return None

    def validate_webhook_signature(self, payload, signature):
        """Validate webhook signature for security"""
        try:
            # Generate expected signature using consumer secret
            expected_signature = hmac.new(
                self.consumer_secret.encode(),
                payload.encode(),
                hashlib.sha256
            ).hexdigest()
            
            return hmac.compare_digest(signature, expected_signature)
        except Exception as e:
            logging.error(f"Webhook signature validation failed: {e}")
            return False

    def process_c2b_payment(self, payment_data):
        """Process incoming C2B payment notification"""
        try:
            # Extract payment details
            transaction_type = payment_data.get('TransactionType', '')
            trans_id = payment_data.get('TransID', '')
            trans_time = payment_data.get('TransTime', '')
            trans_amount = float(payment_data.get('TransAmount', 0))
            business_short_code = payment_data.get('BusinessShortCode', '')
            bill_ref_number = payment_data.get('BillRefNumber', '')
            invoice_number = payment_data.get('InvoiceNumber', '')
            org_account_balance = payment_data.get('OrgAccountBalance', '')
            third_party_trans_id = payment_data.get('ThirdPartyTransID', '')
            msisdn = payment_data.get('MSISDN', '')
            first_name = payment_data.get('FirstName', '')
            middle_name = payment_data.get('MiddleName', '')
            last_name = payment_data.get('LastName', '')

            # Determine payment type based on till number
            if business_short_code == self.license_till:
                payment_type = 'license'
            else:
                payment_type = 'sale'

            return {
                'success': True,
                'payment_type': payment_type,
                'transaction_id': trans_id,
                'amount': trans_amount,
                'phone': msisdn,
                'reference': bill_ref_number,
                'customer_name': f"{first_name} {middle_name} {last_name}".strip(),
                'timestamp': trans_time,
                'business_code': business_short_code
            }

        except Exception as e:
            logging.error(f"Failed to process C2B payment: {e}")
            return {'success': False, 'error': str(e)}

    def get_shop_till_number(self, shop_id):
        """Get till number for a specific shop"""
        # In real implementation, this would fetch from shop settings
        # For now, return a default pattern
        return f"50{shop_id:04d}"  # e.g., 500001, 500002, etc.

# Global instance
mpesa_api = MpesaAPI()
