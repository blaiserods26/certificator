import os
import requests
import matplotlib.font_manager
from threading import Lock

# Store downloaded fonts here
FONTS_DIR = os.path.join(os.getcwd(), "fonts_cache")
os.makedirs(FONTS_DIR, exist_ok=True)

_font_cache_lock = Lock()

def get_google_font_url(font_name):
    """
    Tries to find a download URL for a Google Font.
    This is a heuristic approach since Google Fonts API requires an API key.
    We'll try to use the google-webfonts-helper approach or similar direct links.
    """
    # Simply sanitize the name
    clean_name = font_name.replace(" ", "+")
    # This is a common pattern for Google Fonts cdn, but usually requires more specific file styling
    # A more reliable way without API key is scraping or using a known repository.
    # For this MVP, we will try to fetch from a github mirror or similar if possible,
    # OR we just assume the user might have provided a valid TTF, 
    # BUT the requirement says "get it from google fonts".
    
    # Strategy: Use the Google Fonts Developer API if we had a key, but we don't.
    # Alternative: construct a direct download link often used by downloaders.
    # url = f"https://fonts.google.com/download?family={clean_name}"
    # The above returns a ZIP file. We would need to unzip it.
    
    return f"https://fonts.google.com/download?family={clean_name}"

def download_font(font_name):
    """
    Downloads and extracts the font if not present. Returns path to a TTF/OTF file.
    """
    # Check if we already have it
    sanitized_name = font_name.replace(" ", "_")
    potential_path = os.path.join(FONTS_DIR, sanitized_name)
    
    # If directory exists and has ttf files, return the first one
    if os.path.exists(potential_path):
        for file in os.listdir(potential_path):
            if file.lower().endswith((".ttf", ".otf")):
                return os.path.join(potential_path, file)

    url = get_google_font_url(font_name)
    print(f"Attempting to download font {font_name} from {url}")
    
    try:
        response = requests.get(url, stream=True)
        if response.status_code == 200:
            import zipfile
            import io
            
            with _font_cache_lock:
                z = zipfile.ZipFile(io.BytesIO(response.content))
                extract_path = os.path.join(FONTS_DIR, sanitized_name)
                os.makedirs(extract_path, exist_ok=True)
                z.extractall(extract_path)
                
                # Find the regular font file
                best_font = None
                for file in os.listdir(extract_path):
                    if file.lower().endswith((".ttf", ".otf")):
                        # Prefer "Regular" or just the name
                        if "Regular" in file or file == f"{font_name}.ttf":
                            return os.path.join(extract_path, file)
                        best_font = os.path.join(extract_path, file)
                
                return best_font
    except Exception as e:
        print(f"Failed to download font {font_name}: {e}")
        return None

def get_font_path(font_name):
    """
    Resolves a font name to a file path.
    1. Checks local folder (current dir).
    2. Checks system fonts.
    3. Checks downloaded fonts cache.
    4. Downloads from Google Fonts.
    5. Fallback to default.
    """
    # 1. Local file check (Exact match)
    if os.path.exists(font_name):
        return font_name
    
    local_ttf = f"{font_name}.ttf"
    if os.path.exists(local_ttf):
        return local_ttf

    # 1.5. Local file check (Fuzzy match)
    # Check current directory for files starting with font_name
    curr_dir = os.getcwd()
    for file in os.listdir(curr_dir):
        if file.lower().startswith(font_name.lower()) and file.lower().endswith(('.ttf', '.otf')):
             return os.path.join(curr_dir, file)

    # 2. System fonts (simplistic check)
    try:
        system_fonts = matplotlib.font_manager.findSystemFonts(fontpaths=None, fontext='ttf')
        for f in system_fonts:
            fname = os.path.basename(f)
            # stricter check?
            if font_name.lower() in fname.lower():
                return f
    except:
        pass

    # 3. Check cache or Download
    downloaded_path = download_font(font_name)
    if downloaded_path:
        return downloaded_path
        
    return None
