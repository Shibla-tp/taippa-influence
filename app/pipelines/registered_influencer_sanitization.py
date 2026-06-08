import re

def clean_first_name(name):
    if not isinstance(name, str):
        return ""
    return name.strip().title()

import re

import re

def clean_phone_number(phone):
    if not isinstance(phone, str):
        return ""

    # Remove all non-digit characters
    digits = re.sub(r"\D", "", phone)

    # Normalize Saudi numbers
    if digits.startswith("00966"):
        digits = digits[5:]
    elif digits.startswith("966"):
        digits = digits[3:]
    elif digits.startswith("05"):
        digits = digits[1:]
    elif digits.startswith("5") and len(digits) == 9:
        pass

    # If it looks like a valid Saudi mobile number, format it
    if len(digits) == 9 and digits.startswith("5"):
        return f"+966{digits}"

    # Otherwise return cleaned number with + (if any digits)
    if digits:
        return f"+{digits}"

    return ""




def clean_instagram_handle_name(instagram_handle_name):
    if not instagram_handle_name or not isinstance(instagram_handle_name, str):
        return None

    handle = instagram_handle_name.strip().lower()
    handle = re.sub(r"(https?:\/\/)?(www\.)?(instagram\.com|instagr\.am)\/", "", handle)
    handle = re.split(r"[/?]", handle)[0].strip().rstrip("/")
    handle = handle.lstrip("@")
    
    return f"@{handle}" if handle else None

def clean_tiktok_handle_name(tiktok_handle_name):
    if not tiktok_handle_name or not isinstance(tiktok_handle_name, str):
        return None

    handle = tiktok_handle_name.strip().lower()
    
    # Remove base TikTok URL patterns
    handle = re.sub(r"(https?:\/\/)?(www\.)?tiktok\.com\/(@)?", "", handle)

    # Remove any query parameters or trailing slashes
    handle = re.split(r"[/?]", handle)[0].strip().rstrip("/")

    # Strip any leading @
    handle = handle.lstrip("@")

    return f"@{handle}" if handle else None

def clean_snapchat_handle_name(handle):
    if not handle or not isinstance(handle, str):
        return None

    handle = handle.strip().lower()
    handle = re.sub(r"(https?:\/\/)?(www\.)?(snapchat\.com\/add\/)", "", handle)
    handle = re.split(r"[/?]", handle)[0].strip().rstrip("/")
    handle = handle.lstrip("@")

    return f"@{handle}" if handle else None

def clean_twitter_handle_name(handle):
    if not handle or not isinstance(handle, str):
        return None

    handle = handle.strip().lower()
    handle = re.sub(r"(https?:\/\/)?(www\.)?(twitter\.com\/)", "", handle)
    handle = re.split(r"[/?]", handle)[0].strip().rstrip("/")
    handle = handle.lstrip("@")

    return f"@{handle}" if handle else None

def clean_facebook_handle_name(handle):
    if not handle or not isinstance(handle, str):
        return None

    handle = handle.strip().lower()
    handle = re.sub(r"(https?:\/\/)?(www\.)?(facebook\.com\/)", "", handle)
    handle = re.split(r"[/?]", handle)[0].strip().rstrip("/")
    handle = handle.lstrip("@")

    return f"@{handle}" if handle else None

def clean_location(location):
    if not isinstance(location, str):
        return ""
    location = location.strip().lower()
    if "dammam" in location:
        return "Dammam, KSA"
    elif "riyadh" in location:
        return "Riyadh, KSA"
    elif "jeddah" in location:
        return "Jeddah, KSA"
    return location.title()

def clean_data(data):
    return {
        "first_name": clean_first_name(data.get("first_name", "")),
        "phone_number": clean_phone_number(data.get("phone_number", "")),
        "instagram_handle": clean_instagram_handle_name(data.get("instagram_handle", "")),
        "tiktok_handle": clean_tiktok_handle_name(data.get("tiktok_handle", "")),
        "facebook_handle": clean_facebook_handle_name(data.get("facebook_handle", "")),
        "twitter_handle": clean_twitter_handle_name(data.get("twitter_handle", "")),
        "snapchat_handle": clean_snapchat_handle_name(data.get("snapchat_handle", "")),
        "location": clean_location(data.get("location", ""))
    }
