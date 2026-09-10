import os
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import math

WIDTH = 1920
HEIGHT = 1080
FPS = 30
TOTAL_FRAMES = 600

# Fonts
FONT_TITLE = ImageFont.truetype("C:/Windows/Fonts/segoeuib.ttf", 28)
FONT_STAGE = ImageFont.truetype("C:/Windows/Fonts/segoeuib.ttf", 17)
FONT_HEADING = ImageFont.truetype("C:/Windows/Fonts/segoeuib.ttf", 15)
FONT_BODY = ImageFont.truetype("C:/Windows/Fonts/segoeui.ttf", 13)
FONT_SMALL = ImageFont.truetype("C:/Windows/Fonts/segoeui.ttf", 11)
FONT_CODE = ImageFont.truetype("C:/Windows/Fonts/consola.ttf", 14)
FONT_CODE_SM = ImageFont.truetype("C:/Windows/Fonts/consola.ttf", 12)
FONT_BADGE = ImageFont.truetype("C:/Windows/Fonts/segoeuib.ttf", 11)

# Color Palette
BG_COLOR = (11, 19, 41)
GRID_COLOR = (30, 41, 59)
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
    
    # Left face (y-plane)
    draw_iso_polygon(draw, [p000, p010, p011, p001], ox, oy, scale, left_color, edge_color, edge_width)
    # Right face (x-plane)
    draw_iso_polygon(draw, [p010, p110, p111, p011], ox, oy, scale, right_color, edge_color, edge_width)
    # Top face (z-plane)
    draw_iso_polygon(draw, [p001, p101, p111, p011], ox, oy, scale, top_color, edge_color, edge_width)

def draw_iso_platform(draw, x, y, z, dx, dy, dz, ox, oy, scale,
                      top_fill=(18, 30, 56), side_fill=(10, 18, 35), border_color=(56, 189, 248, 120)):
    # Draw drop shadow
    shadow_pts = [
        iso_project(x-5, y-5, z-2, ox, oy, scale),
        iso_project(x+dx+5, y-5, z-2, ox, oy, scale),
        iso_project(x+dx+5, y+dy+5, z-2, ox, oy, scale),
        iso_project(x-5, y+dy+5, z-2, ox, oy, scale),
    ]
    draw.polygon(shadow_pts, fill=(5, 10, 20, 180))
    
    # 3D block
    draw_iso_block(draw, x, y, z, dx, dy, dz, ox, oy, scale,
                   top_color=top_fill, left_color=side_fill, right_color=(side_fill[0]+4, side_fill[1]+4, side_fill[2]+6),
                   edge_color=border_color, edge_width=1)

def draw_server_rack(draw, x, y, z, ox, oy, scale, status_color=EMERALD, pulse=0.0):
    # Base server chassis
    draw_iso_block(draw, x, y, z, 70, 70, 120, ox, oy, scale,
                   top_color=(35, 45, 65), left_color=(20, 28, 42), right_color=(12, 18, 30),
                   edge_color=(60, 75, 100), edge_width=1)
    
    # Draw server blades / rack units
    for u in range(4):
        bz = z + 15 + u * 24
        # Left face indicator slots
        draw_iso_block(draw, x+2, y+2, bz, 66, 66, 18, ox, oy, scale,
                       top_color=(45, 55, 78), left_color=(28, 38, 55), right_color=(18, 25, 40),
                       edge_color=(70, 90, 120), edge_width=1)
        
        # LED indicators on front/right face
        p_led = iso_project(x + 68, y + 15 + u*12, bz + 9, ox, oy, scale)
        led_col = status_color if (u % 2 == 0 or pulse > 0.5) else (CYAN if status_color == EMERALD else status_color)
        draw.ellipse([p_led[0]-2.5, p_led[1]-2.5, p_led[0]+2.5, p_led[1]+2.5], fill=led_col)
        
        p_led2 = iso_project(x + 68, y + 35 + u*6, bz + 9, ox, oy, scale)
        draw.ellipse([p_led2[0]-2, p_led2[1]-2, p_led2[0]+2, p_led2[1]+2], fill=(56, 189, 248) if u != 3 else (34, 197, 94))
    
    # Server top fan / status logo
    p_top = iso_project(x + 35, y + 35, z + 120, ox, oy, scale)
    draw.ellipse([p_top[0]-14, p_top[1]-7, p_top[0]+14, p_top[1]+7], outline=(234, 88, 12), width=2, fill=(40, 25, 20))
    draw.ellipse([p_top[0]-6, p_top[1]-3, p_top[0]+6, p_top[1]+3], fill=(249, 115, 22))

def draw_db_cylinder(draw, x, y, z, radius, height, ox, oy, scale, fill_col=(28, 45, 80), pulse=0.0):
    steps = 16
    rad30 = math.radians(30)
    cos30 = math.cos(rad30)
    sin30 = math.sin(rad30)
    
    # Rings
    for level in [0, height*0.33, height*0.66, height]:
        pts = []
        for i in range(steps):
            angle = 2 * math.pi * i / steps
            px_raw = x + radius * math.cos(angle)
            py_raw = y + radius * math.sin(angle)
            pz_raw = z + level
            pts.append(iso_project(px_raw, py_raw, pz_raw, ox, oy, scale))
        draw.polygon(pts, fill=(35, 55, 95) if level == height else (22, 35, 65), outline=(56, 189, 248, 180), width=1)
    
    # Pulse wave indicator on SQL DB
    if pulse > 0:
        p_center = iso_project(x, y, z + height*0.5, ox, oy, scale)
        p_rad = int(radius * scale * 0.7 * (1 + pulse*0.3))
        draw.ellipse([p_center[0]-p_rad, p_center[1]-int(p_rad*0.5), p_center[0]+p_rad, p_center[1]+int(p_rad*0.5)],
                     outline=(56, 189, 248, int(200*(1-pulse))), width=2)

print("Helper draw functions compiled.")
