import yaml
import streamlit_authenticator as stauth

# পাসওয়ার্ড লিস্ট
passwords = ['niloy123', 'lipi456']

# হ্যাশ তৈরি করা
hashed_passwords = stauth.Hasher.hash_list(passwords)

# YAML ফাইলের স্ট্রাকচার তৈরি করা
config = {
    'credentials': {
        'usernames': {
            'niloy': {
                'email': 'niloy@example.com',
                'name': 'Niloy',
                'password': hashed_passwords[0]
            },
            'lipi': {
                'email': 'lipi@example.com',
                'name': 'Lipi',
                'password': hashed_passwords[1]
            }
        }
    },
    'cookie': {
        'expiry_days': 30,
        'key': 'some_random_signature_key_lipi',
        'name': 'lipi_trade_cookie'
    },
    'pre-authorized': {
        'emails': ['niloy@example.com']
    }
}

# সরাসরি config.yaml ফাইলে লিখে ফেলা
with open('config.yaml', 'w', encoding='utf-8') as file:
    yaml.dump(config, file, default_flow_style=False, allow_unicode=True)

print("✅ সফলভাবে config.yaml ফাইলটি তৈরি হয়েছে!")