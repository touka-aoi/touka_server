from hashlib import blake2b
from base64 import urlsafe_b64encode
from argon2 import low_level


def create_encryption_key(_id: str, _password: str):
    """暗号化キーを作成する

    Args:
        _id (str): ユーザーID
        _password (str): パスワード

    Returns:
        str: 暗号化キー
    """
    encryption_key: str = get_access_key(_id, _password)
    return encryption_key
    

def argon_hash(id: str, password: str, size: int, domain: str) -> str:
    """ハッシュ化関数

    Args:
        id (str): ユーザーID
        password (str): パスワード
        size (int): ハッシュ長
        domain (str): ドメイン名

    Returns:
        str: ハッシュ化文字列
    """
    pre_salt: str = password[:6] + id + domain

    # salt 
    blake = blake2b(digest_size=16) #ハッシュインスタンス作成
    blake.update(pre_salt.encode()) #ハッシュ更新
    salt: bytes = blake.digest() # バイト列出力
    
    raw: bytes = low_level.hash_secret_raw(password.encode(), salt, 2, int(2000000/1024), 1, size, low_level.Type.ID) # ハッシュ生成
    hashed: str = urlsafe_b64encode(raw).decode() #base64でエンコード, str化

    return hashed

def get_access_key(id: str, password: str) -> str:
    """暗号化キーを取得する

    Args:
        id (str): ユーザーID
        password (str): パスワード

    Returns:
        str: 暗号化キー
    """
    return argon_hash(id, password, 64, "novelai_data_access_key")[:64]
