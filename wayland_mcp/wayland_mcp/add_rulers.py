from PIL import Image, ImageDraw, ImageFont
import os

def add_rulers(input_path, output_path=None):
    """Add measurement rulers to an image"""
    # Settings - defined first to avoid scope issues
    ruler_size = 30            # Increased to ensure text fits
    major_tick_interval = 100  # Pixel interval for major ticks
    mid_tick_interval = 50     # Added mid ticks
    minor_tick_interval = 10   # Pixel interval for minor ticks
    major_tick_length = 8      # Length of major tick marks
    mid_tick_length = 6        # Mid tick length
    minor_tick_length = 3      # Length of minor tick marks
    ruler_color = "#555"       # Dark gray instead of red
    bg_color = "#f0f0f0"       # Light gray background

    if output_path is None:
        output_path = input_path
        
    # Open image
    orig_img = Image.open(input_path)
    orig_width, orig_height = orig_img.size
    
    # Create new image with space for rulers
    new_width = orig_width + ruler_size
    new_height = orig_height + ruler_size
    img = Image.new("RGB", (new_width, new_height), bg_color)
    
    # Paste original image offset by ruler size
    img.paste(orig_img, (ruler_size, ruler_size))
    
    # Create drawing context
    draw = ImageDraw.Draw(img)
    
    # Font handling - two sizes for major/mid ticks
    try:
        major_font = ImageFont.truetype("DejaVuSans.ttf", 10)
        mid_font = ImageFont.truetype("DejaVuSans.ttf", 8)
    except:
        major_font = ImageFont.load_default()
        mid_font = major_font
    
    # Add horizontal ruler (top)
    for x in range(0, orig_width, minor_tick_interval):
        is_major = x % major_tick_interval == 0
        is_mid = x % mid_tick_interval == 0
        if is_major or is_mid:
            tick_len = major_tick_length if is_major else mid_tick_length
            font = major_font if is_major else mid_font
            # Draw tick mark
            draw.line((x + ruler_size, ruler_size - tick_len,
                      x + ruler_size, ruler_size), fill=ruler_color, width=1)
            # Center text below tick
            text = str(x)
            text_width = font.getlength(text)
            draw.text((x + ruler_size - text_width/2,
                      ruler_size - tick_len - font.size - 2),
                     text, fill=ruler_color, font=font)
        else:
            tick_len = minor_tick_length
            draw.line((x + ruler_size, ruler_size - tick_len,
                      x + ruler_size, ruler_size), fill=ruler_color, width=1)
    
    # Add vertical ruler (left)
    for y in range(0, orig_height, minor_tick_interval):
        is_major = y % major_tick_interval == 0
        is_mid = y % mid_tick_interval == 0
        if is_major or is_mid:
            tick_len = major_tick_length if is_major else mid_tick_length
            font = major_font if is_major else mid_font
            # Draw tick mark
            draw.line((ruler_size - tick_len, y + ruler_size,
                      ruler_size, y + ruler_size), fill=ruler_color, width=1)
            # Center text vertically, align left with padding
            text = str(y)
            text_width = font.getlength(text)
            text_x = max(2, ruler_size - tick_len - text_width - 2)  # Ensure visibility
            text_y = y + ruler_size - font.size//2
            draw.text((text_x, text_y), text, fill=ruler_color, font=font)
        else:
            tick_len = minor_tick_length
            draw.line((ruler_size - tick_len, y + ruler_size,
                      ruler_size, y + ruler_size), fill=ruler_color, width=1)
    
    # Save result
    img.save(output_path)
    return output_path

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        add_rulers(sys.argv[1])
    else:
        print("Usage: python add_rulers.py screenshot.png")