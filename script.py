from PIL import Image, ImageDraw, ImageFont
import pandas as pd
import os
import zipfile
from utils.fonts import get_font_path, download_font

def generate_certificates(template_path, csv_path, output_dir, field_configs):
    """
    Generates certificates based on CSV and Template with dynamic fields.
    
    Args:
        template_path (str): Path to template image.
        csv_path (str): Path to CSV file.
        output_dir (str): Directory to save certificates.
        field_configs (list): List of dicts, e.g.:
            [
                {
                    "column": "name",
                    "font": "Arial",
                    "size": 90,
                    "color": (r, g, b),
                    "x": 100,
                    "y": 200
                },
                ...
            ]
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Load CSV
    try:
        df = pd.read_csv(csv_path)
        # Normalize column names to strip whitespace
        df.columns = [c.strip() for c in df.columns]
    except Exception as e:
        return None, f"Error reading CSV: {e}"

    # Load Template
    try:
        template = Image.open(template_path)
    except Exception as e:
        return None, f"Error opening template: {e}"

    # Pre-load fonts to avoid loading them in the loop
    loaded_fonts = {}
    for config in field_configs:
        font_name = config.get('font', 'Arial')
        font_size = int(config.get('size', 40))
        key = (font_name, font_size)
        
        if key not in loaded_fonts:
            font_path = get_font_path(font_name)
            if not font_path:
                print(f"Dowloading font: {font_name}")
                font_path = download_font(font_name)
            
            try:
                if font_path:
                    loaded_fonts[key] = ImageFont.truetype(font_path, font_size)
                else:
                    # Fallback to a scalable font if possible, else default
                    # Try typical windows fonts or just fallback to default (which is tiny)
                    # Let's try to find ANY ttf in the folder
                    fallback = "arial.ttf"
                    try:
                        loaded_fonts[key] = ImageFont.truetype(fallback, font_size)
                    except:
                        # try looking for any ttf in current dir
                        ttfs = [f for f in os.listdir('.') if f.endswith('.ttf')]
                        if ttfs:
                             loaded_fonts[key] = ImageFont.truetype(ttfs[0], font_size)
                        else:
                             print(f"Warning: Could not load any font for {font_name}, taking default.")
                             loaded_fonts[key] = ImageFont.load_default()
            except Exception as e:
                print(f"Error loading font {font_name}: {e}")
                loaded_fonts[key] = ImageFont.load_default()

    generated_files = []

    for idx, row in df.iterrows():
        # Create copy
        img = template.copy()
        draw = ImageDraw.Draw(img)
        
        # Use a reliable filename
        # Try to find a 'name' or 'email' column for the filename, else use index
        filename_base = f"certificate_{idx}"
        for col in df.columns:
            if 'name' in col.lower():
                val = str(row[col]).strip()
                if val:
                    filename_base = "".join(x for x in val if x.isalnum() or x in (' ', '_', '-')).replace(" ", "_")
                    break

        for config in field_configs:
            col_name = config.get('column')
            if col_name not in df.columns:
                continue
                
            text = str(row[col_name]).strip()
            if not text or text == 'nan':
                continue

            font = loaded_fonts.get((config.get('font'), int(config.get('size'))))
            color = config.get('color', (0, 0, 0))
            x = int(config.get('x', 0))
            y = int(config.get('y', 0))
            alignment = config.get('alignment', 'center')

            if alignment == 'center':
                # Determine text width to center it manually or use anchor
                # Using anchor='mm' (middle-middle) or 'mt' (middle-top)
                # Ensure the frontend coordinates correspond to the anchor.
                # If frontend sends center-coordinates, use 'mm' or 'ms'.
                # Let's assume (x,y) is the point the user dragged. 
                # If they selected Center, they dragged the Center point.
                # So we draw with anchor='mm' (middle vertical, middle horizontal)
                # OR 'ma' (middle ascender). 'mm' is safer for general centering.
                # However, previous code used (x,y) as top-left of the bbox sometimes.
                # Let's try anchor='mm'
                try:
                    draw.text((x, y), text, font=font, fill=color, anchor="mm")
                except ValueError:
                    # Fallback for older PIL versions without anchor support (pre 9.0ish?)
                    bbox = draw.textbbox((0, 0), text, font=font)
                    w = bbox[2] - bbox[0]
                    h = bbox[3] - bbox[1]
                    draw.text((x - w / 2, y - h / 2), text, font=font, fill=color)
            elif alignment == 'right':
                try:
                    draw.text((x, y), text, font=font, fill=color, anchor="rm")
                except ValueError:
                    bbox = draw.textbbox((0, 0), text, font=font)
                    w = bbox[2] - bbox[0]
                    h = bbox[3] - bbox[1]
                    draw.text((x - w, y - h / 2), text, font=font, fill=color)
            else:
                # Left align: treat (x, y) as the left-middle anchor point.
                try:
                    draw.text((x, y), text, font=font, fill=color, anchor="lm")
                except ValueError:
                    # Fallback
                    bbox = draw.textbbox((0, 0), text, font=font)
                    h = bbox[3] - bbox[1]
                    draw.text((x, y - h / 2), text, font=font, fill=color)

        # Save
        out_path = os.path.join(output_dir, f"{filename_base}.pdf")
        
        img = img.convert("RGB")
        img.save(out_path, "PDF", resolution=300.0)
        generated_files.append(out_path)

    # Create ZIP
    if not generated_files:
        return None, "No certificates generated. Check CSV data."

    zip_filename = "certificates.zip"
    zip_path = os.path.join(output_dir, zip_filename)
    with zipfile.ZipFile(zip_path, 'w') as zipf:
        for file in generated_files:
            zipf.write(file, os.path.basename(file))
            
    return zip_path, None
