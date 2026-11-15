"""
christmas_tree.py — renders a 20s vertical (1080x1920, 30fps) video of a
rotating 3D ASCII christmas tree, drawn character-cell by character-cell,
with this very source file scrolling in a code editor underneath.

usage:  python christmas_tree.py [--out tree.mp4] [--handle @you] [--preview]
needs:  numpy, pillow, ffmpeg on PATH
"""
import argparse, math, re, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

# ---------------------------------------------------------------- config
W, H, FPS, DURATION = 1080, 1920, 30, 20.0
TOP_H = int(H * 0.6)                 # ascii night sky (top 60%)
CW, CH = 12, 22                      # character cell size in px
COLS, ROWS = W // CW, TOP_H // CH    # 90 x 52 cells
GROUND_ROW = ROWS - 7
SCALE = 830                          # world units -> px
TEXT = "MERRYCHRISTMASJOOJOO"
N_BULBS = 176
FONT_DIR = "/usr/share/fonts/truetype/jetbrains-mono/"
FONT = FONT_DIR + "JetBrainsMono-Regular.ttf"
FONT_B = FONT_DIR + "JetBrainsMono-Bold.ttf"

GREEN = np.array([60, 210, 95])
GOLD = np.array([255, 200, 70])
RED = np.array([235, 45, 60])
SNOW = np.array([225, 235, 255])
TRUNK = np.array([140, 85, 40])


def smooth(a, b, t):
    """smoothstep from a to b"""
    x = min(max((t - a) / (b - a), 0.0), 1.0)
    return x * x * (3 - 2 * x)


# ---------------------------------------------------------- glyph atlas
GLYPHS = sorted(set(TEXT + " .*+o@#\u25cf|/\\-_~=[]:'`^"))
GI = {c: i for i, c in enumerate(GLYPHS)}


def build_atlas():
    font = ImageFont.truetype(FONT_B, 18)
    atlas = np.zeros((len(GLYPHS), CH, CW), np.float32)
    for i, c in enumerate(GLYPHS):
        im = Image.new("L", (CW, CH))
        ImageDraw.Draw(im).text((CW / 2, CH / 2), c, 255, font, anchor="mm")
        atlas[i] = np.asarray(im) / 255.0
    return atlas


# -------------------------------------------------------- tree geometry
TIERS = [  # (y_bottom, y_top, r_bottom, r_top)
    (0.08, 0.46, 0.42, 0.10),
    (0.36, 0.70, 0.32, 0.06),
    (0.60, 0.92, 0.22, 0.00),
]


def envelope(y):
    """outer radius of the tree at height y (max over tiers)"""
    r = 0.0
    for y0, y1, r0, r1 in TIERS:
        if y0 <= y <= y1:
            f = (y - y0) / (y1 - y0)
            r = max(r, (r0 + (r1 - r0) * f) * (1 - 0.16 * ((f * 4) % 1)))
    return r


def build_tree():
    """sample the tiered cone surface; each point carries a letter that
    stays glued to the surface, so the text visibly wraps around in 3D"""
    P, N, CHR, COL = [], [], [], []
    for y0, y1, r0, r1 in TIERS:
        slope = (r0 - r1) / (y1 - y0)
        for y in np.arange(y0, y1, 0.0035):
            f = (y - y0) / (y1 - y0)
            r = (r0 + (r1 - r0) * f) * (1 - 0.16 * ((f * 4) % 1))  # branch layers
            around = max(1, int(2 * math.pi * r * SCALE / CW))      # cells around
            th = np.linspace(0, 2 * math.pi, max(8, around * 5), endpoint=False)
            band = int(y * SCALE / CH)
            P.append(np.stack([r * np.cos(th), np.full_like(th, y), r * np.sin(th)], 1))
            N.append(np.stack([np.cos(th), np.full_like(th, slope), np.sin(th)], 1))
            k = (th / (2 * math.pi) * around).astype(int)
            CHR.append(np.array([GI[TEXT[(band * 7 + kk) % len(TEXT)]] for kk in k]))
            COL.append(np.tile(GREEN, (len(th), 1)))
    for y in np.arange(0.0, 0.10, 0.004):                         # trunk
        th = np.linspace(0, 2 * math.pi, 40, endpoint=False)
        P.append(np.stack([0.05 * np.cos(th), np.full_like(th, y), 0.05 * np.sin(th)], 1))
        N.append(np.stack([np.cos(th), np.zeros_like(th), np.sin(th)], 1))
        CHR.append(np.full(len(th), GI["|"]))
        COL.append(np.tile(TRUNK, (len(th), 1)))
    P, N = np.concatenate(P), np.concatenate(N)
    N /= np.linalg.norm(N, axis=1, keepdims=True)
    return P, N, np.concatenate(CHR), np.concatenate(COL).astype(np.float32)


def build_garland():
    u = np.linspace(0, 1, N_BULBS)
    y = 0.10 + u * 0.80
    th = u * 2 * math.pi * 6.5
    r = np.array([envelope(v) for v in y]) + 0.03
    return np.stack([r * np.cos(th), y, r * np.sin(th)], 1)


def build_ornaments(rng, n=30):
    y = rng.uniform(0.12, 0.84, n)
    th = rng.uniform(0, 2 * math.pi, n)
    r = np.array([envelope(v) for v in y]) + 0.025
    pos = np.stack([r * np.cos(th), y, r * np.sin(th)], 1)
    order = np.argsort(y)                                       # pop bottom-up
    return pos[order], np.array([RED, GOLD] * (n // 2))[:n]


# ------------------------------------------------------------ projection
LIGHT = np.array([-0.6, 0.65, 0.55]); LIGHT /= np.linalg.norm(LIGHT)


def project(p, angle):
    """yaw around y, slight downward camera pitch -> (col, row, depth)"""
    c, s = math.cos(angle), math.sin(angle)
    x = p[:, 0] * c + p[:, 2] * s
    z = -p[:, 0] * s + p[:, 2] * c
    ys = p[:, 1] - z * 0.12
    persp = 1.0 / (1.0 - z * 0.25)
    col = (COLS / 2 + x * persp * SCALE / CW).astype(int)
    row = (GROUND_ROW - ys * persp * SCALE / CH).astype(int)
    return col, row, z


def rotate_normals(n, angle):
    c, s = math.cos(angle), math.sin(angle)
    return np.stack([n[:, 0] * c + n[:, 2] * s, n[:, 1], -n[:, 0] * s + n[:, 2] * c], 1)


def splat(grid_c, grid_k, grid_z, col, row, z, chars, colors):
    """z-buffered write of points into the character grid"""
    ok = (col >= 0) & (col < COLS) & (row >= 0) & (row < ROWS)
    col, row, z, chars, colors = col[ok], row[ok], z[ok], chars[ok], colors[ok]
    o = np.argsort(z)                      # far -> near, near writes last
    col, row, z, chars, colors = col[o], row[o], z[o], chars[o], colors[o]
    front = z >= grid_z[row, col]
    col, row = col[front], row[front]
    grid_z[row, col] = z[front]
    grid_k[row, col] = chars[front]
    grid_c[row, col] = colors[front]


def put(grid_c, grid_k, r, c, ch, color):
    if 0 <= r < ROWS and 0 <= c < COLS and ch != " ":
        grid_k[r, c] = GI[ch]
        grid_c[r, c] = color


# ------------------------------------------------------------- the scene
class Scene:
    def __init__(self, handle):
        rng = np.random.default_rng(7)
        self.handle = handle
        self.atlas = build_atlas()
        self.P, self.N, self.CHR, self.COL = build_tree()
        self.garland = build_garland()
        self.orn, self.orn_col = build_ornaments(rng)
        self.snow = np.stack([rng.uniform(0, COLS, 240), rng.uniform(0, ROWS, 240),
                              rng.uniform(1.5, 4.5, 240), rng.uniform(0, 6.3, 240)], 1)
        self.sky_stars = np.stack([rng.integers(0, COLS, 60), rng.integers(0, GROUND_ROW - 8, 60),
                                   rng.uniform(0, 6.3, 60)], 1)
        self.ground = rng.random((ROWS - GROUND_ROW, COLS))
        yy = np.linspace(0, 1, TOP_H)[:, None, None]
        self.sky = (np.array([4, 6, 22]) * (1 - yy) + np.array([14, 20, 48]) * yy) \
            * np.ones((1, W, 1))
        self.gifts = [(-28, 9, 5, RED, GOLD), (-18, 7, 4, np.array([70, 140, 255]), SNOW),
                      (14, 8, 5, GOLD, RED), (24, 10, 4, np.array([170, 80, 230]), GOLD)]
        self.f_big = ImageFont.truetype(FONT_B, 58)
        self.f_hud = ImageFont.truetype(FONT, 26)
        self.f_timer = ImageFont.truetype(FONT_B, 40)
        self.editor = Editor(open(__file__).read().splitlines())

    # ----------------------------------------------------- ascii layer
    def ascii_frame(self, t):
        vis = 1 - smooth(19.4, 20.0, t)                  # fade out -> loops
        gc = np.zeros((ROWS, COLS, 3), np.float32)
        gk = np.full((ROWS, COLS), GI[" "])
        gz = np.full((ROWS, COLS), -9.0)
        stats = {"angle": 0, "bulbs": 0, "chars": 0}

        intro = smooth(0.0, 1.5, t) * vis
        for x, y, ph in self.sky_stars:                 # twinkling sky
            b = 0.25 + 0.25 * math.sin(t * 2 + ph)
            put(gc, gk, int(y), int(x), "." if b < 0.4 else "+", SNOW * b * intro)
        for x, y, sp, ph in self.snow:                  # falling snow
            r = int((y + sp * t) % ROWS)
            c = int(x + 1.2 * math.sin(t * 0.8 + ph)) % COLS
            ch = "*" if sp > 3.8 else ("+" if sp > 2.7 else ".")
            put(gc, gk, r, c, ch, SNOW * (0.45 + sp / 9) * intro)
        for r in range(GROUND_ROW + 1, ROWS):           # snowy ground
            for c in range(COLS):
                v = self.ground[r - GROUND_ROW, c]
                ch = "~" if r == GROUND_ROW + 1 else ("_" if v > 0.7 else ("." if v > 0.3 else " "))
                put(gc, gk, r, c, ch, SNOW * (0.35 + 0.25 * v) * intro)

        angle = t * 0.55
        stats["angle"] = int(math.degrees(angle)) % 360
        grow = smooth(2.0, 7.0, t)                      # tree grows bottom-up
        if grow > 0:
            m = self.P[:, 1] <= grow * 0.93
            col, row, z = project(self.P[m], angle)
            n = rotate_normals(self.N[m], angle)
            shade = 0.10 + 0.95 * np.clip(n @ LIGHT, 0, 1) ** 1.3
            tip = np.clip(1 - (grow * 0.93 - self.P[m, 1]) / 0.05, 0, 1) * (grow < 1)
            color = self.COL[m] * shade[:, None] + 120 * tip[:, None]
            splat(gc, gk, gz, col, row, z, self.CHR[m], color * vis)

        nb = int(N_BULBS * smooth(7.0, 11.0, t))        # spiral garland
        stats["bulbs"] = nb
        if nb:
            col, row, z = project(self.garland[:nb], angle)
            tw = 0.75 + 0.25 * np.sin(t * 6 + np.arange(nb) * 1.7)
            splat(gc, gk, gz, col, row, z, np.full(nb, GI["\u25cf"]),
                  (GOLD * tw[:, None]).astype(np.float32) * 1.25 * vis)

        no = int(len(self.orn) * smooth(11.0, 13.0, t)) # ornaments
        if no:
            col, row, z = project(self.orn[:no], angle)
            splat(gc, gk, gz, col, row, z, np.full(no, GI["@"]),
                  self.orn_col[:no].astype(np.float32) * 1.3 * vis)

        star = smooth(13.0, 14.0, t)                    # star on top
        if star > 0:
            col, row, _ = project(np.array([[0, 0.96, 0]]), angle)
            pulse = (1.2 + 0.3 * math.sin(t * 5)) * star * vis
            for dr, dc, ch in [(0, 0, "*"), (0, -1, "-"), (0, 1, "-"), (-1, 0, "|"), (1, 0, "|"),
                               (-1, -1, "\\"), (-1, 1, "/"), (1, -1, "/"), (1, 1, "\\"),
                               (0, -2, "="), (0, 2, "=")]:
                put(gc, gk, row[0] + dr, col[0] + dc, ch, GOLD * pulse)

        for i, (x, w, h, body, ribbon) in enumerate(self.gifts):   # gifts drop in
            p = smooth(14.0 + i * 0.4, 14.6 + i * 0.4, t)
            if p <= 0:
                continue
            drop = int((1 - p) * 14)
            c0, r1 = COLS // 2 + x, GROUND_ROW + 2 - drop
            for r in range(r1 - h, r1):
                for c in range(c0, c0 + w):
                    edge = r == r1 - h or c in (c0, c0 + w - 1) or r == r1 - 1
                    mid = c == c0 + w // 2 or r == r1 - h + 1
                    ch = "[" if c == c0 else "]" if c == c0 + w - 1 else ("=" if r == r1 - h else
                         "+" if (mid and c == c0 + w // 2 and r == r1 - h + 1) else
                         "|" if c == c0 + w // 2 else "-" if mid else "#")
                    put(gc, gk, r, c, ch, (ribbon if mid else body) * (1.1 if edge else 0.85) * vis)

        stats["chars"] = int((gk != GI[" "]).sum())
        return gc, gk, stats

    def render_cells(self, gc, gk):
        g = self.atlas[gk][..., None] * gc[:, :, None, None, :]     # R,C,h,w,3
        img = g.transpose(0, 2, 1, 3, 4).reshape(ROWS * CH, COLS * CW, 3)
        out = self.sky.copy()
        oy, ox = (TOP_H - ROWS * CH) // 2, (W - COLS * CW) // 2
        out[oy:oy + ROWS * CH, ox:ox + COLS * CW] += img
        return out

    def bloom(self, arr):
        bright = np.clip(arr - 150, 0, 255).astype(np.uint8)
        small = Image.fromarray(bright).resize((W // 4, TOP_H // 4), Image.BILINEAR)
        glow = small.filter(ImageFilter.GaussianBlur(5)).resize((W, TOP_H), Image.BILINEAR)
        return arr + np.asarray(glow, np.float32) * 1.6

    # ----------------------------------------------------------- frame
    def frame(self, i):
        t = i / FPS
        gc, gk, stats = self.ascii_frame(t)
        top = self.bloom(self.render_cells(gc, gk))
        img = Image.new("RGB", (W, H))
        img.paste(Image.fromarray(np.clip(top, 0, 255).astype(np.uint8)), (0, 0))

        vis = 1 - smooth(19.4, 20.0, t)
        msg = "MERRY CHRISTMAS 2026"                     # typed greeting
        n = int(len(msg) * smooth(16.0, 18.5, t))
        if n and vis > 0:
            txt = msg[:n] + ("_" if int(t * 3) % 2 == 0 and n < len(msg) else "")
            layer = Image.new("RGB", (W, 150))
            ImageDraw.Draw(layer).text((W // 2, 75), txt, (255, 215, 60), self.f_big, anchor="mm")
            glow = layer.filter(ImageFilter.GaussianBlur(10))
            arr = np.asarray(layer, np.float32) + np.asarray(glow, np.float32) * 1.5
            region = np.asarray(img.crop((0, 10, W, 160)), np.float32)
            img.paste(Image.fromarray(np.clip(region + arr * vis, 0, 255).astype(np.uint8)), (0, 10))

        d = ImageDraw.Draw(img)                         # HUD overlays
        d.text((W - 36, 210), f"{int(t // 60):02d}:{t % 60:05.2f}", (255, 215, 60),
               self.f_timer, anchor="ra")
        hud = (120, 200, 140)
        d.text((36, 210), f"rot   {stats['angle']:3d}°", hud, self.f_hud)
        d.text((36, 244), f"bulbs {stats['bulbs']:3d}/{N_BULBS}", hud, self.f_hud)
        d.text((36, 278), f"chars {stats['chars']:4d}", hud, self.f_hud)
        d.text((36, TOP_H - 50), self.handle, (230, 230, 240), self.f_hud)

        img.paste(self.editor.render(t), (0, TOP_H))
        return img


# --------------------------------------------------------- code editor
class Editor:
    KW = r"\b(def|class|return|for|in|if|else|elif|import|from|as|with|while|and|or|not|None|True|False|lambda|self)\b"
    TOKEN = re.compile(r"(#.*$)|(\"\"\"|'[^']*'|\"[^\"]*\")|" + KW + r"|(\b\d+\.?\d*\b)|(\b\w+(?=\())")
    COLORS = {1: (106, 153, 85), 2: (206, 145, 120), 3: (197, 134, 192), 4: (181, 206, 168), 5: (220, 220, 170)}

    def __init__(self, lines):
        self.font = ImageFont.truetype(FONT, 22)
        self.fb = ImageFont.truetype(FONT_B, 22)
        self.lh, self.h = 31, H - TOP_H
        self.sheet = Image.new("RGB", (W, self.lh * len(lines) + self.h), (24, 26, 33))
        d = ImageDraw.Draw(self.sheet)
        in_doc = False
        for n, line in enumerate(lines):
            y = n * self.lh + 6
            d.text((60, y), f"{n + 1:3d}", (90, 96, 110), self.font, anchor="ra")
            if in_doc or line.lstrip().startswith('"""'):
                d.text((80, y), line, self.COLORS[2], self.font)
                if line.count('"""') == 1:
                    in_doc = not in_doc
                continue
            x, pos = 80, 0
            for m in self.TOKEN.finditer(line):
                x = self._run(d, x, y, line[pos:m.start()], (212, 212, 212))
                x = self._run(d, x, y, m.group(0), self.COLORS[m.lastindex])
                pos = m.end()
            self._run(d, x, y, line[pos:], (212, 212, 212))
        self.n = len(lines)

    def _run(self, d, x, y, s, color):
        d.text((x, y), s, color, self.font)
        return x + self.font.getlength(s)

    def render(self, t):
        bar = 52
        view = self.h - bar
        span = self.n * self.lh - view
        off = int(span * smooth(0.5, 19.4, t))           # slow scroll
        img = Image.new("RGB", (W, self.h), (24, 26, 33))
        img.paste(self.sheet.crop((0, off, W, off + view)), (0, bar))
        d = ImageDraw.Draw(img)
        d.rectangle((0, 0, W, bar), (34, 37, 46))
        for k, c in enumerate([(255, 95, 86), (255, 189, 46), (39, 201, 63)]):
            d.ellipse((24 + k * 30, 18, 40 + k * 30, 34), c)
        d.text((130, 26), "christmas_tree.py", (200, 204, 214), self.fb, anchor="lm")
        blink = (60, 230, 110) if int(t * 2) % 2 == 0 else (30, 110, 55)
        d.ellipse((W - 268, 19, W - 254, 33), blink)
        d.text((W - 244, 26), "running · 30 fps", (60, 230, 110), self.font, anchor="lm")
        hl = bar + view // 2                             # "executing" line band
        band = Image.new("RGBA", (W, self.lh), (80, 140, 255, 28))
        img.paste(band, (0, hl), band)
        d.line((0, bar, W, bar), (50, 54, 66), 2)
        return img


# ----------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="christmas_tree.mp4")
    ap.add_argument("--handle", default="@joojoo")
    ap.add_argument("--preview", action="store_true", help="save a few PNG frames only")
    a = ap.parse_args()
    scene = Scene(a.handle)
    total = int(DURATION * FPS)
    if a.preview:
        for s in (1, 4, 6, 9, 12, 15, 18, 19.8):
            scene.frame(int(s * FPS)).save(f"preview_{s:04.1f}s.png")
        return
    ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo",
                           "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                           "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18",
                           "-preset", "medium", "-movflags", "+faststart", a.out],
                          stdin=subprocess.PIPE)
    for i in range(total):
        ff.stdin.write(scene.frame(i).tobytes())
        if i % 30 == 0:
            print(f"\rframe {i}/{total}", end="", file=sys.stderr)
    ff.stdin.close()
    ff.wait()
    print(f"\nwrote {a.out}", file=sys.stderr)


if __name__ == "__main__":
    main()
