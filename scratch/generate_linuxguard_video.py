import os
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import math

WIDTH = 1920
HEIGHT = 1080
FPS = 30
TOTAL_FRAMES = 600 # 20.0 seconds

# Typography
FONT_TITLE = ImageFont.truetype("C:/Windows/Fonts/segoeuib.ttf", 26)
FONT_SUBTITLE = ImageFont.truetype("C:/Windows/Fonts/segoeui.ttf", 15)
FONT_STAGE = ImageFont.truetype("C:/Windows/Fonts/segoeuib.ttf", 15)
FONT_STAGE_SM = ImageFont.truetype("C:/Windows/Fonts/segoeui.ttf", 12)
FONT_HEADING = ImageFont.truetype("C:/Windows/Fonts/segoeuib.ttf", 15)
FONT_BODY = ImageFont.truetype("C:/Windows/Fonts/segoeui.ttf", 13)
FONT_BODY_BOLD = ImageFont.truetype("C:/Windows/Fonts/segoeuib.ttf", 13)
FONT_SMALL = ImageFont.truetype("C:/Windows/Fonts/segoeui.ttf", 11)
FONT_SMALL_BOLD = ImageFont.truetype("C:/Windows/Fonts/segoeuib.ttf", 11)
FONT_CODE = ImageFont.truetype("C:/Windows/Fonts/consola.ttf", 13)
FONT_CODE_BOLD = ImageFont.truetype("C:/Windows/Fonts/consolab.ttf", 14) if os.path.exists("C:/Windows/Fonts/consolab.ttf") else FONT_CODE
FONT_CODE_SM = ImageFont.truetype("C:/Windows/Fonts/consola.ttf", 11)

# Enterprise Color Palette matching architecture_3d.jpg
BG_TOP = (11, 19, 41)
BG_BOTTOM = (15, 23, 42)

TEXT_WHITE = (248, 250, 252)
TEXT_MUTED = (148, 163, 184)
TEXT_DIM = (100, 116, 139)

CYAN = (56, 189, 248)
BLUE = (59, 130, 246)
INDIGO = (99, 102, 241)
EMERALD = (16, 185, 129)
GREEN = (34, 197, 94)
AMBER = (245, 158, 11)
RED = (239, 68, 68)
ORANGE = (249, 115, 22)
PURPLE = (168, 85, 247)
SLATE_900 = (15, 23, 42)
SLATE_800 = (30, 41, 59)
SLATE_700 = (51, 65, 85)
SLATE_600 = (71, 85, 105)

# Pre-generate gradient background
def generate_base_background(w, h):
    base = np.zeros((h, w, 3), dtype=np.uint8)
    for y in range(h):
        r = y / h
        base[y, :, 0] = int(BG_TOP[0] * (1 - r) + BG_BOTTOM[0] * r)
        base[y, :, 1] = int(BG_TOP[1] * (1 - r) + BG_BOTTOM[1] * r)
        base[y, :, 2] = int(BG_TOP[2] * (1 - r) + BG_BOTTOM[2] * r)
    img = Image.fromarray(base)
    draw = ImageDraw.Draw(img, 'RGBA')
    
    # Subtle isometric grid in background
    for gx in range(-1200, 2400, 80):
        # Line 1 (30 deg)
        p1 = (gx, 0)
        p2 = (gx + int(HEIGHT * math.tan(math.radians(60))), HEIGHT)
        draw.line([p1, p2], fill=(30, 41, 59, 35), width=1)
        
        # Line 2 (-30 deg)
        p3 = (gx, 0)
        p4 = (gx - int(HEIGHT * math.tan(math.radians(60))), HEIGHT)
        draw.line([p3, p4], fill=(30, 41, 59, 35), width=1)
        
    return img

BASE_BG = generate_base_background(WIDTH, HEIGHT)

def iso_project(x, y, z, ox=960, oy=540, scale=1.0):
    rad = math.radians(30)
    cos30 = math.cos(rad)
    sin30 = math.sin(rad)
    px = ox + (x - y) * cos30 * scale
    py = oy + (x + y) * sin30 * scale - z * scale
    return (px, py)

def draw_iso_polygon(draw, points_3d, ox, oy, scale, fill_color, outline_color=None, width=1):
    pts_2d = [iso_project(x, y, z, ox, oy, scale) for (x, y, z) in points_3d]
    draw.polygon(pts_2d, fill=fill_color)
    if outline_color:
        draw.line(pts_2d + [pts_2d[0]], fill=outline_color, width=width)

def draw_iso_block(draw, x, y, z, dx, dy, dz, ox=960, oy=540, scale=1.0,
                   top_color=(51, 65, 85), left_color=(30, 41, 59), right_color=(15, 23, 42),
                   edge_color=(71, 85, 105), edge_width=1):
    p000 = (x, y, z)
    p100 = (x + dx, y, z)
    p110 = (x + dx, y + dy, z)
    p010 = (x, y + dy, z)
    p001 = (x, y, z + dz)
    p101 = (x + dx, y, z + dz)
    p111 = (x + dx, y + dy, z + dz)
    p011 = (x, y + dy, z + dz)
    
    draw_iso_polygon(draw, [p000, p010, p011, p001], ox, oy, scale, left_color, edge_color, edge_width)
    draw_iso_polygon(draw, [p010, p110, p111, p011], ox, oy, scale, right_color, edge_color, edge_width)
    draw_iso_polygon(draw, [p001, p101, p111, p011], ox, oy, scale, top_color, edge_color, edge_width)

def draw_rounded_card(draw, x1, y1, x2, y2, radius=8, fill=(20, 30, 50, 220), outline=(56, 189, 248, 80), width=1):
    draw.rounded_rectangle([x1, y1, x2, y2], radius=radius, fill=fill, outline=outline, width=width)

def draw_hud_gauge(draw, x, y, w, h, label, val_text, pct, color=CYAN, bg_col=(30, 41, 59)):
    draw_rounded_card(draw, x, y, x+w, y+h, radius=6, fill=(15, 23, 42, 230), outline=(color[0], color[1], color[2], 90))
    draw.text((x+8, y+6), label, fill=TEXT_MUTED, font=FONT_SMALL)
    draw.text((x+w-8, y+6), val_text, fill=color, font=FONT_SMALL_BOLD, anchor="ra")
    
    # Progress bar
    bar_y = y + h - 8
    draw.rounded_rectangle([x+8, bar_y, x+w-8, bar_y+4], radius=2, fill=bg_col)
    pct_w = max(2, int((w-16) * min(1.0, max(0.0, pct))))
    draw.rounded_rectangle([x+8, bar_y, x+8+pct_w, bar_y+4], radius=2, fill=color)

def draw_flow_particle(draw, p_start, p_end, progress, color=CYAN, size=4):
    cur_x = p_start[0] + (p_end[0] - p_start[0]) * progress
    cur_y = p_start[1] + (p_end[1] - p_start[1]) * progress
    
    # Trail
    for t in range(1, 5):
        t_prog = max(0.0, progress - t * 0.05)
        tx = p_start[0] + (p_end[0] - p_start[0]) * t_prog
        ty = p_start[1] + (p_end[1] - p_start[1]) * t_prog
        alpha = int(180 / (t + 1))
        draw.ellipse([tx-size*0.6, ty-size*0.6, tx+size*0.6, ty+size*0.6], fill=(color[0], color[1], color[2], alpha))
        
    # Main glowing particle
    draw.ellipse([cur_x-size, cur_y-size, cur_x+size, cur_y+size], fill=(255, 255, 255, 255))
    draw.ellipse([cur_x-size*1.5, cur_y-size*1.5, cur_x+size*1.5, cur_y+size*1.5], fill=(color[0], color[1], color[2], 140))

print("Core generator module loaded.")
