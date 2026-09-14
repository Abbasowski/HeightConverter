"""Generate icon.ico — a height-ruler icon matching the app's purple/cyan theme."""
from PIL import Image, ImageDraw

S = 1024
img = Image.new('RGBA', (S, S), (0, 0, 0, 0))

# --- gradient background (dark indigo -> purple), rounded square ---
top, bot = (23, 18, 51, 255), (139, 92, 246, 255)
grad = Image.new('RGBA', (S, S))
gd = ImageDraw.Draw(grad)
for y in range(S):
    t = y / (S - 1)
    c = tuple(int(top[i] + (bot[i] - top[i]) * t) for i in range(4))
    gd.line([(0, y), (S, y)], fill=c)

mask = Image.new('L', (S, S), 0)
ImageDraw.Draw(mask).rounded_rectangle([0, 0, S - 1, S - 1], radius=230, fill=255)
img.paste(grad, (0, 0), mask)

d = ImageDraw.Draw(img)

# --- white vertical ruler bar ---
rx0, rx1 = S // 2 - 72, S // 2 + 72
ry0, ry1 = 140, 884
d.rounded_rectangle([rx0, ry0, rx1, ry1], radius=64, fill=(238, 240, 255, 255))

# --- tick marks on both edges (long every 4th) ---
tick = (23, 18, 51, 255)
n = 16
for i in range(n + 1):
    y = ry0 + 70 + i * (ry1 - ry0 - 140) / n
    length = 78 if i % 4 == 0 else 44
    # left edge ticks
    d.rounded_rectangle([rx0 + 12, y - 8, rx0 + 12 + length, y + 8], radius=8, fill=tick)
    # right edge ticks
    d.rounded_rectangle([rx1 - 12 - length, y - 8, rx1 - 12, y + 8], radius=8, fill=tick)

# --- small cyan accent dot (matches app accent) ---
d.ellipse([S // 2 - 26, 96, S // 2 + 26, 148], fill=(34, 211, 238, 255))

img.save('icon.ico', sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
img.resize((256, 256), Image.LANCZOS).save('icon_preview.png')
print('icon.ico + icon_preview.png written')
