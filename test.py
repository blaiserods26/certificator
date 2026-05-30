from PIL import Image, ImageDraw, ImageFont
import pandas as pd
import os

# Paths
TEMPLATE_PATH = "certificate.png"
CSV_PATH = "participants.csv"
OUTPUT_DIR = "certificates"

os.makedirs(OUTPUT_DIR, exist_ok=True)

# Load template once
template = Image.open(TEMPLATE_PATH)
W, H = template.size

# Load CSV (you'll use this later for looping)
df = pd.read_csv(CSV_PATH)

# Fonts (you can change these)
# For best look: use PlayfairDisplay-Bold.ttf for name, Roboto-Bold.ttf for institute
NAME_FONT_PATH = "Charm-Regular.ttf"
INSTITUTE_FONT_PATH = "Charm-Bold.ttf"

NAME_FONT_SIZE = 90       # a bit bigger for the name
INSTITUTE_FONT_SIZE = 72  # slightly smaller for institute

# Colors
GOLD = (140, 106, 36)     # matches the certificate style

# Test data
name = "Dr. Mukesh Kalla"
institute = "ICFAI University Jaipur"

# Create a copy of the template
img = template.copy()
draw = ImageDraw.Draw(img)

name_font = ImageFont.truetype(NAME_FONT_PATH, NAME_FONT_SIZE)
inst_font = ImageFont.truetype(INSTITUTE_FONT_PATH, INSTITUTE_FONT_SIZE)

# ----- Draw NAME (centered) -----
text = name
bbox = draw.textbbox((0, 0), text, font=name_font)
w = bbox[2] - bbox[0]
h = bbox[3] - bbox[1]

x = (W - w) / 2
y = H * 0.30   # a bit below 1/3 of page; tweak if needed

draw.text((x, y), text, font=name_font, fill=GOLD)

# ----- Draw INSTITUTE (centered) -----
text = institute
bbox = draw.textbbox((0, 0), text, font=inst_font)
w = bbox[2] - bbox[0]
h = bbox[3] - bbox[1]

x = (W - w) / 2
y = H * 0.415   # just under the name; tweak if needed

draw.text((x, y), text, font=inst_font, fill=GOLD)

# Save as PDF
safe_name = name.replace(" ", "_")
out_path = os.path.join(OUTPUT_DIR, f"{safe_name}.pdf")

img = img.convert("RGB")
img.save(out_path, "PDF", resolution=300.0)

print(f"Created {out_path}")
