from PIL import Image, ImageDraw, ImageTk

def create_status_icon(cover_status, lyrics_status, is_loading=False):
    # cover_status: 0=None (Red), 1=BadSize (Yellow), 2=Good (Green)
    # lyrics_status: 0=None (Red), 1=Unsynced (Yellow), 2=Synced (Green)
    
    # Layout Configuration: Split Status Layout
    # Total width 100px. Two 50px zones.
    # We want "floating" badges with whitespace.
    width = 100
    height = 16
    
    img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    colors = {0: '#ff4444', 1: '#ffbb33', 2: '#00C851'}
    
    # Text Color Logic
    def get_text_color(bg_code):
        if bg_code == 1: # Yellow
            return 'black'
        return 'white'

    # Badge Configuration
    badge_w = 20
    badge_h = 14 # Slightly smaller than 16 to have top/bottom margin? Or full height? 
                 # User said "floating", so let's make them slightly smaller than full height or just full height but narrow.
                 # Let's go with full height 16px for simplicity, but narrow width.
    badge_h = 16
    
    # --- Zone 1: Cover (0-50px) ---
    # Center is 25. Badge width 20.
    # x1 = 25 - 10 = 15
    # x2 = 25 + 10 = 35
    c_x1, c_x2 = 15, 35
    
    c_color = colors.get(cover_status, '#ff4444')
    draw.rectangle([c_x1, 0, c_x2, badge_h], fill=c_color)
    
    c_text_color = get_text_color(cover_status)
    # Center text 'C' in the badge
    # Text width approx 8px. Center of badge is 25. Start at 21.
    draw.text((21, 1), "C", fill=c_text_color)
    
    # --- Zone 2: Lyrics (50-100px) ---
    # Center is 75. Badge width 20.
    # x1 = 75 - 10 = 65
    # x2 = 75 + 10 = 85
    l_x1, l_x2 = 65, 85
    
    if is_loading:
        l_color = '#33b5e5' # Blue
        l_text_color = 'white'
    else:
        l_color = colors.get(lyrics_status, '#ff4444')
        l_text_color = get_text_color(lyrics_status)
        
    draw.rectangle([l_x1, 0, l_x2, badge_h], fill=l_color)
    # Center text 'L' in the badge
    # Center of badge is 75. Start at 71.
    draw.text((71, 1), "L", fill=l_text_color)
    
    return ImageTk.PhotoImage(img)
