"""
Yardımcı Fonksiyonlar
Genel kullanım için utility fonksiyonları
"""

import hashlib
import uuid
import json
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta
import re

logger = logging.getLogger(__name__)


def generate_unique_id() -> str:
    """Benzersiz ID oluştur"""
    return str(uuid.uuid4())


def hash_string(text: str) -> str:
    """String hash'le"""
    return hashlib.sha256(text.encode()).hexdigest()


def validate_email(email: str) -> bool:
    """Email formatını doğrula"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def sanitize_filename(filename: str) -> str:
    """Dosya adını güvenli hale getir"""
    # Tehlikeli karakterleri kaldır
    filename = re.sub(r'[<>:"/\\|?*]', '', filename)
    # Boşlukları tire ile değiştir
    filename = re.sub(r'\s+', '-', filename)
    # Birden fazla tireyi tek tireye çevir
    filename = re.sub(r'-+', '-', filename)
    return filename.strip('-')


def format_duration(seconds: float) -> str:
    """Süreyi okunabilir formata çevir"""
    if seconds < 60:
        return f"{seconds:.2f}s"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f}m"
    else:
        hours = seconds / 3600
        return f"{hours:.1f}h"


def parse_json_safe(json_string: str) -> Optional[Dict[str, Any]]:
    """JSON string'i güvenli şekilde parse et"""
    try:
        return json.loads(json_string)
    except (json.JSONDecodeError, TypeError):
        logger.warning(f"Geçersiz JSON string: {json_string}")
        return None


def flatten_dict(d: Dict[str, Any], parent_key: str = '', sep: str = '_') -> Dict[str, Any]:
    """Nested dictionary'yi düzleştir"""
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)


def chunk_list(lst: List[Any], chunk_size: int) -> List[List[Any]]:
    """Listeyi chunk'lara böl"""
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]


def calculate_percentage(part: int, total: int) -> float:
    """Yüzde hesapla"""
    if total == 0:
        return 0.0
    return (part / total) * 100


def is_valid_url(url: str) -> bool:
    """URL formatını doğrula"""
    pattern = r'^https?://(?:[-\w.])+(?:[:\d]+)?(?:/(?:[\w/_.])*(?:\?(?:[\w&=%.])*)?(?:#(?:[\w.])*)?)?$'
    return re.match(pattern, url) is not None


def extract_domain(url: str) -> Optional[str]:
    """URL'den domain çıkar"""
    try:
        from urllib.parse import urlparse
        parsed = urlparse(url)
        return parsed.netloc
    except Exception:
        return None


def format_file_size(size_bytes: int) -> str:
    """Dosya boyutunu okunabilir formata çevir"""
    if size_bytes == 0:
        return "0B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f}{size_names[i]}"


def generate_random_string(length: int = 8) -> str:
    """Rastgele string oluştur"""
    import random
    import string
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(length))


def mask_sensitive_data(data: str, mask_char: str = '*') -> str:
    """Hassas verileri maskele"""
    # Email maskeleme
    if '@' in data:
        parts = data.split('@')
        if len(parts) == 2:
            username, domain = parts
            if len(username) > 2:
                masked_username = username[0] + mask_char * (len(username) - 2) + username[-1]
            else:
                masked_username = mask_char * len(username)
            return f"{masked_username}@{domain}"
    
    # Telefon numarası maskeleme
    if re.match(r'^\+?[\d\s\-\(\)]+$', data):
        if len(data) > 4:
            return data[:2] + mask_char * (len(data) - 4) + data[-2:]
    
    # Genel maskeleme
    if len(data) > 4:
        return data[:2] + mask_char * (len(data) - 4) + data[-2:]
    
    return mask_char * len(data)


def retry_on_exception(func, max_retries: int = 3, delay: float = 1.0):
    """Hata durumunda tekrar dene decorator"""
    import time
    
    def wrapper(*args, **kwargs):
        for attempt in range(max_retries):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if attempt == max_retries - 1:
                    raise e
                logger.warning(f"Fonksiyon hatası (deneme {attempt + 1}/{max_retries}): {e}")
                time.sleep(delay * (2 ** attempt))  # Exponential backoff
        return None
    
    return wrapper


def validate_required_fields(data: Dict[str, Any], required_fields: List[str]) -> List[str]:
    """Gerekli alanları doğrula"""
    missing_fields = []
    for field in required_fields:
        if field not in data or data[field] is None or data[field] == "":
            missing_fields.append(field)
    return missing_fields


def deep_merge_dicts(dict1: Dict[str, Any], dict2: Dict[str, Any]) -> Dict[str, Any]:
    """İki dictionary'yi derinlemesine birleştir"""
    result = dict1.copy()
    for key, value in dict2.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge_dicts(result[key], value)
        else:
            result[key] = value
    return result


def get_nested_value(data: Dict[str, Any], path: str, default: Any = None) -> Any:
    """Nested dictionary'den değer al"""
    keys = path.split('.')
    current = data
    
    for key in keys:
        if isinstance(current, dict) and key in current:
            current = current[key]
        else:
            return default
    
    return current


def set_nested_value(data: Dict[str, Any], path: str, value: Any) -> None:
    """Nested dictionary'ye değer ata"""
    keys = path.split('.')
    current = data
    
    for key in keys[:-1]:
        if key not in current:
            current[key] = {}
        current = current[key]
    
    current[keys[-1]] = value


def remove_nested_key(data: Dict[str, Any], path: str) -> bool:
    """Nested dictionary'den anahtar kaldır"""
    keys = path.split('.')
    current = data
    
    for key in keys[:-1]:
        if isinstance(current, dict) and key in current:
            current = current[key]
        else:
            return False
    
    if isinstance(current, dict) and keys[-1] in current:
        del current[keys[-1]]
        return True
    
    return False 