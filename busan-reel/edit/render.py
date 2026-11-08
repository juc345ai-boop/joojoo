#!/usr/bin/env python3
"""Busan edit that follows the reference reel's cut timeline (24 fps, 41.32 s).

Usage: render.py [preview|segments|final]
  preview  -> one graded still per shot, tiled, to check framing
  segments -> render every shot as an intermediate clip
  final    -> concat + grain + reference audio -> final mp4
"""
import os, sys, subprocess
from concurrent.futures import ThreadPoolExecutor

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FOOT = os.path.join(ROOT, 'footage')
REEL = os.path.join(ROOT, 'reel', 'reel.mp4')
OUT = os.path.join(ROOT, 'edit')
SEG = os.path.join(OUT, 'segs')
FPS = 24
TOTAL = 41.32
GRADE = ("eq=saturation=0.74:gamma=0.9:contrast=1.03,"
         "curves=master='0/0.03 0.2/0.15 0.5/0.45 0.8/0.79 1/0.9',"
         "colorbalance=rs=-0.01:gs=0.01:bs=0.025:rm=0.035:gm=0.012:bm=-0.03:rh=0.035:gh=0.015:bh=-0.035,"
         "unsharp=5:5:-0.35")

# Reference cut points (scene detection on the reel), seconds.
CUTS = [0.0, 0.1667, 0.3333, 0.4167, 0.5, 0.6667, 0.75, 0.9167, 1.0, 1.5, 2.5,
        3.6667, 3.9167, 5.0833, 5.7917, 6.7083, 7.3333, 7.625, 9.1667, 9.4167,
        10.1667, 11.8333, 14.875, 15.0417, 15.2083, 15.375, 15.5417, 15.7083,
        15.875, 16.0417, 16.2083, 16.25, 17.1667, 17.5833, 18.0417, 18.5,
        19.9583, 20.375, 21.2083, 21.75, 22.6667, 23.0417, 23.4583, 23.9583,
        24.9167, 25.4167, 26.2083, 26.6667, 26.8333, 27.0, 27.1667, 27.3333,
        27.5, 27.6667, 28.125, 28.5, 29.0, 29.4583, 29.8333, 30.75, 31.625,
        34.7917, 35.25, 35.75, 36.25, 36.625, 37.125, 37.5833, 38.0, 38.5,
        38.9583, 39.4167, 40.2917, 40.75, TOTAL]

# One entry per segment between CUTS:
# (source, t_in, speed, zoom_start, zoom_end, pan_x 0..1, pan_y 0..1)
# source: clip id in footage/ (mp4), 'pNN' photo, or 'FLASH'
S = [
    # --- intro: 2-frame detail flashes ---
    ('0007', 0.30, 1, 3.0, 3.0, 0.97, 0.38),   # Take/떡갈비 sign
    ('p20',  0.00, 1, 2.2, 2.2, 0.50, 0.12),   # menu board
    ('0008', 11.5, 1, 2.6, 2.6, 0.92, 0.85),   # stall food
    ('0008', 1.00, 1, 2.6, 2.6, 0.45, 0.05),   # market signs
    ('0056', 3.00, 1, 2.6, 2.6, 0.50, 0.08),   # night lights
    ('0071', 1.00, 1, 2.6, 2.6, 0.30, 0.55),   # harbour boats
    ('0087', 2.00, 1, 3.0, 3.0, 0.55, 0.22),   # station board
    ('0063', 4.20, 1, 1.6, 1.6, 0.50, 0.50),   # bus blur
    ('p18',  0.00, 1, 1.8, 1.9, 0.72, 0.56),   # 돼지국밥 sign
    # --- verse 1 ---
    ('0008', 15.0, 1, 1.6, 1.6, 0.50, 1.00),   # legs walking
    ('0087', 0.50, 1, 1.0, 1.08, 0.5, 0.5),    # station hall
    ('0088', 3.00, 1, 1.15, 1.15, 0.5, 0.80),  # room, bags
    ('0056', 0.20, 1, 1.0, 1.06, 0.5, 0.5),    # night stairs
    ('0008', 11.3, 1, 1.3, 1.3, 0.50, 0.45),   # stall worker
    ('0071', 3.80, 1, 1.0, 1.0, 0.5, 0.5),     # street pan
    ('0008', 2.00, 1, 1.1, 1.1, 0.5, 0.5),     # crowd
    ('0016', 0.80, 1, 1.4, 1.4, 0.30, 0.40),   # food court
    ('0007', 6.80, 1, 1.0, 1.08, 0.5, 0.5),    # colourful market
    ('p19',  0.00, 1, 1.0, 1.04, 0.5, 0.60),   # hallway photo
    ('0087', 6.00, 1, 1.15, 1.15, 0.40, 0.60), # station seats
    ('0008', 4.50, 1, 1.0, 1.06, 0.5, 0.5),    # crowd towards camera
    ('0071', 0.00, 0.8, 1.0, 1.1, 0.5, 0.5),   # HARBOUR breath
    # --- burst 1 (4 frames each) ---
    ('0007', 1.60, 1, 1.6, 1.6, 0.80, 0.40),
    ('0008', 7.50, 1, 1.5, 1.5, 0.50, 0.50),
    ('0016', 5.00, 1, 1.5, 1.5, 0.60, 0.50),
    ('0007', 11.0, 1, 1.5, 1.5, 0.50, 0.50),
    ('0008', 13.2, 1, 1.6, 1.6, 0.40, 0.60),
    ('0056', 2.80, 1, 1.6, 1.6, 0.60, 0.40),
    ('0007', 14.0, 1, 1.5, 1.5, 0.30, 0.50),
    ('0008', 16.2, 1, 1.5, 1.5, 0.50, 0.50),
    ('FLASH', 0, 1, 1, 1, 0, 0),               # 1-frame light flash
    # --- verse 2 ---
    ('0016', 2.80, 1, 1.0, 1.05, 0.5, 0.5),    # red/green food court
    ('0056', 4.20, 1, 1.5, 1.5, 0.50, 0.20),   # neon
    ('0008', 9.00, 1, 1.3, 1.3, 0.30, 0.50),
    ('0007', 15.6, 1, 1.2, 1.2, 0.5, 0.5),
    ('0008', 10.6, 1, 1.1, 1.15, 0.5, 0.5),    # stall people
    ('p20',  0.00, 1, 1.0, 1.04, 0.5, 0.5),    # restaurant table
    ('0056', 1.20, 1, 1.2, 1.2, 0.5, 0.5),
    ('0063', 2.40, 1, 1.2, 1.2, 0.5, 0.5),
    ('0063', 5.30, 1, 1.0, 1.0, 0.5, 0.5),     # window
    ('0001', 1.50, 1, 1.6, 1.6, 0.50, 0.30),   # ceiling TV
    ('0007', 3.20, 1, 2.2, 2.2, 0.97, 0.35),   # big sign
    ('0007', 4.20, 1, 1.0, 1.0, 0.5, 0.5),
    ('0008', 6.40, 1, 1.15, 1.15, 0.5, 0.5),
    ('0071', 2.20, 1, 1.6, 1.6, 0.70, 0.60),   # harbour detail
    ('0087', 7.20, 1, 1.1, 1.1, 0.5, 0.5),
    ('0016', 6.50, 1, 1.2, 1.2, 0.5, 0.5),
    # --- burst 2: food details ---
    ('0008', 11.0, 1, 2.4, 2.4, 0.05, 0.90),
    ('0008', 12.3, 1, 2.0, 2.0, 0.15, 0.95),
    ('p20',  0.00, 1, 2.4, 2.4, 0.85, 0.70),
    ('0008', 13.0, 1, 2.4, 2.4, 0.45, 0.80),
    ('0007', 0.80, 1, 2.4, 2.4, 0.90, 0.45),
    ('0016', 1.50, 1, 2.4, 2.4, 0.20, 0.30),
    # --- verse 3 ---
    ('0008', 7.00, 1, 1.3, 1.3, 0.50, 0.40),
    ('0056', 2.30, 1, 1.6, 1.6, 0.40, 0.30),
    ('0071', 4.60, 1, 1.0, 1.0, 0.5, 0.5),
    ('0071', 5.60, 1, 1.2, 1.2, 0.50, 0.40),
    ('0087', 8.50, 1, 1.3, 1.3, 0.5, 0.5),
    ('0063', 0.00, 1, 1.0, 1.0, 0.5, 0.5),
    ('0063', 3.40, 1, 1.1, 1.1, 0.5, 0.5),
    ('0007', 9.60, 0.8, 1.0, 1.08, 0.5, 0.5),  # CORRIDOR breath
    # --- outro run ---
    ('0007', 16.2, 1, 1.3, 1.3, 0.5, 0.5),
    ('0008', 16.8, 1, 1.1, 1.1, 0.5, 0.5),
    ('0008', 0.40, 1, 1.0, 1.0, 0.5, 0.5),
    ('0016', 4.00, 1, 1.3, 1.3, 0.5, 0.5),
    ('0056', 5.40, 1, 1.2, 1.2, 0.5, 0.5),
    ('0007', 5.50, 1, 1.2, 1.2, 0.5, 0.5),
    ('0087', 3.80, 1, 1.0, 1.0, 0.5, 0.5),
    ('0008', 3.20, 1, 1.2, 1.2, 0.5, 0.5),
    ('0008', 11.6, 1, 1.4, 1.4, 0.5, 0.5),
    ('0016', 0.20, 1, 1.0, 1.0, 0.5, 0.5),
    ('0071', 0.90, 1, 1.2, 1.3, 0.5, 0.35),    # sea + sky
    ('0056', 5.80, 1, 1.0, 1.0, 0.5, 0.5),
    ('0056', 0.00, 1, 1.1, 1.15, 0.5, 0.5),    # last shot
]
assert len(S) == len(CUTS) - 1, (len(S), len(CUTS))

FR = [round(c * FPS) for c in CUTS]


def src_path(src):
    if src.startswith('p'):
        return os.path.join(FOOT, src + '.jpg')
    return os.path.join(FOOT, src + '.mp4')


def vf(z0, z1, px, py, nframes):
    dur = max(nframes / FPS, 1e-3)
    z = f"({z0}+({z1}-{z0})*min(t/{dur:.4f},1))" if z0 != z1 else f"{z0}"
    return (f"scale=w='2*trunc(960*{z}+0.5)':h=-2:eval=frame:flags=bicubic,"
            f"crop=1920:1080:x='(iw-1920)*{px}':y='(ih-1080)*{py}',setsar=1,"
            f"{GRADE},format=yuv420p")


def cmd_for(i, still=None):
    src, tin, speed, z0, z1, px, py = S[i]
    n = FR[i + 1] - FR[i]
    out = still or os.path.join(SEG, f'{i:03d}.mp4')
    base = ['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y']
    if src == 'FLASH':
        inp = ['-f', 'lavfi', '-i', 'color=c=0xFFE2B8:s=1920x1080:r=24']
        chain = 'format=yuv420p'
    elif src.startswith('p'):
        inp = ['-loop', '1', '-framerate', str(FPS), '-i', src_path(src)]
        chain = vf(z0, z1, px, py, n)
    else:
        need = n / FPS * speed + 0.3
        inp = ['-ss', f'{tin:.3f}', '-t', f'{need:.3f}', '-i', src_path(src)]
        chain = (f"setpts=(PTS-STARTPTS)/{speed},fps={FPS},"
                 + vf(z0, z1, px, py, n))
    if still:
        return base + inp + ['-vf', chain + ',scale=384:216,'
                             f"drawtext=text='{i} {src}':x=4:y=4:fontsize=16:"
                             "fontcolor=yellow:box=1:boxcolor=black",
                             '-frames:v', '1', out]
    return base + inp + ['-vf', chain, '-an', '-frames:v', str(n), '-r', str(FPS),
                         '-c:v', 'libx264', '-preset', 'fast', '-crf', '12',
                         '-pix_fmt', 'yuv420p', out]


def run(c):
    r = subprocess.run(c, capture_output=True, text=True)
    if r.returncode:
        print('FAIL', ' '.join(c[-1:]), r.stderr[-500:])
    return r.returncode


def frames_of(p):
    r = subprocess.run(['ffprobe', '-v', 'error', '-count_frames', '-select_streams', 'v:0',
                        '-show_entries', 'stream=nb_read_frames', '-of', 'csv=p=0', p],
                       capture_output=True, text=True)
    return int(r.stdout.strip() or 0)


def main(mode):
    os.makedirs(SEG, exist_ok=True)
    if mode == 'preview':
        pv = os.path.join(OUT, 'pv')
        os.makedirs(pv, exist_ok=True)
        with ThreadPoolExecutor(4) as ex:
            list(ex.map(run, [cmd_for(i, os.path.join(pv, f'{i:03d}.jpg')) for i in range(len(S))]))
        run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-pattern_type', 'glob',
             '-i', os.path.join(pv, '*.jpg'), '-vf', 'tile=10x8', '-frames:v', '1',
             os.path.join(OUT, 'preview.jpg')])
    elif mode == 'segments':
        with ThreadPoolExecutor(3) as ex:
            list(ex.map(run, [cmd_for(i) for i in range(len(S))]))
        bad = []
        for i in range(len(S)):
            want = FR[i + 1] - FR[i]
            got = frames_of(os.path.join(SEG, f'{i:03d}.mp4'))
            if got != want:
                bad.append((i, want, got))
        print('frame mismatches:', bad)
    elif mode == 'final':
        lst = os.path.join(OUT, 'list.txt')
        with open(lst, 'w') as f:
            for i in range(len(S)):
                f.write(f"file '{os.path.join(SEG, f'{i:03d}.mp4')}'\n")
        total_frames = FR[-1]
        fade_st = (total_frames - 10) / FPS
        out = os.path.join(OUT, 'busan_like_reel.mp4')
        run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y',
             '-f', 'concat', '-safe', '0', '-i', lst, '-i', REEL,
             '-map', '0:v', '-map', '1:a',
             '-vf', f"vignette=angle=PI/5.5,noise=alls=3:allf=t,fade=t=out:st={fade_st:.3f}:d={10/FPS:.3f},format=yuv420p",
             '-af', f"afade=t=out:st={TOTAL-0.6:.2f}:d=0.6",
             '-c:v', 'libx264', '-preset', 'slow', '-b:v', '7M', '-maxrate', '9M',
             '-bufsize', '14M', '-x264-params', 'aq-mode=3', '-profile:v', 'high',
             '-level', '4.1', '-pix_fmt', 'yuv420p', '-r', str(FPS),
             '-c:a', 'aac', '-b:a', '192k', '-ar', '48000',
             '-movflags', '+faststart', '-t', f'{TOTAL:.3f}', out])
        print(out)


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else 'preview')
