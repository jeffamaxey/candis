import hashlib

def modify_data_path(username):
    hash_val = hashlib.sha256(username.encode()).hexdigest()
    return f'{hash_val}_data'
