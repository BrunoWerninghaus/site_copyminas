from werkzeug.security import generate_password_hash, check_password_hash

def hash_password(password):
    """Criptografa uma senha usando werkzeug"""
    return generate_password_hash(password, method='pbkdf2:sha256')

def check_password(hashed_password, password):
    """Verifica se a senha está correta"""
    return check_password_hash(hashed_password, password)
