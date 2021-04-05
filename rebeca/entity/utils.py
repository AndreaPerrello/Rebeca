import hashlib


def get_id_from_dict(d: dict, salt: str):
    unique_str = f'{salt}:' + '-'.join([f"{key}:{val}" for key, val in sorted(d.items())])
    return hashlib.sha1(unique_str.encode('utf-8')).hexdigest()


def get_id_from_list(l: list, salt: str):
    unique_str = f'{salt}:' + '-'.join([f"{v}" for v in sorted(l)])
    return hashlib.sha1(unique_str.encode('utf-8')).hexdigest()
