#!/usr/bin/env python3
"""Busan edit #3: follows the third reference reel (warm film grade, intro box
zoom, 3x3 grid collage, vertical-strip split screen, whip blurs, white flashes),
24 fps, 16.88 s.

Usage: render3.py [preview|segments|final]
"""
import os, sys, subprocess
from concurrent.futures import ThreadPoolExecutor

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FOOT = os.path.join(ROOT, 'footage')
REEL = os.path.join(ROOT, 'reel3', 'reel.mp4')
OUT = os.path.join(ROOT, 'edit3')
SEG = os.path.join(OUT, 'segs')
FPS = 24
TOTAL = 16.878
W, H = 1920, 1080

GRADE = ("eq=saturation=0.88:gamma=0.85:contrast=1.1,"
         "curves=r='0/0.03 0.5/0.57 1/1':g='0/0.02 0.5/0.5 1/0.94':b='0/0.03 0.5/0.38 1/0.76',"
         "colorbalance=rs=-0.01:bs=0.02:rm=0.04:bm=-0.04:rh=0.06:gh=0.03:bh=-0.07")

CUTS = [0.0, 1.333, 3.167, 3.208, 4.25, 4.75, 5.0, 5.417, 5.75, 6.0, 6.25,
        6.75, 6.792, 8.792, 10.042, 11.25, 11.833, 12.583, 13.292, 14.0,
        14.708, 15.375, TOTAL]
FR = [round(c * FPS) for c in CUTS]

# (source, t_in, speed, zoom_start, zoom_end, pan_x, pan_y, fx)
# fx: '' | 'intro' (box zoom from 1/3 size) | 'grid' | 'strips' | 'stripout'
#     | 'whip' | 'white'
S = [
    ('0008', 6.00, 1, 1.0, 1.04, 0.5, 0.5, 'intro'),   # main shot + captions
    ('0008', 7.33, 1, 1.04, 1.04, 0.5, 0.5, 'grid'),   # 3x3 collage
    ('WHITE', 0, 1, 1, 1, 0, 0, 'white'),
    ('0007', 10.0, 1, 1.0, 1.05, 0.5, 0.5, ''),        # corridor walk
    ('0008', 15.0, 1, 1.1, 1.1, 0.5, 0.5, ''),         # crowd
    ('0071', 3.30, 1, 1.0, 1.0, 0.5, 0.5, 'whip'),
    ('0071', 3.60, 1, 1.0, 1.0, 0.5, 0.5, ''),         # street
    ('0008', 1.70, 1, 1.0, 1.0, 0.5, 0.5, 'whip'),
    ('0008', 2.00, 1, 1.0, 1.0, 0.5, 0.5, ''),         # market crowd
    ('0016', 0.70, 1, 1.6, 1.6, 0.62, 0.35, 'whip'),
    ('0016', 1.00, 1, 1.6, 1.6, 0.62, 0.35, ''),       # 돼지국밥 sign
    ('WHITE', 0, 1, 1, 1, 0, 0, 'white'),
    ('0071', 0.00, 1, 1.0, 1.05, 0.5, 0.5, 'strips'),  # harbour + vertical strips
    ('0007', 12.0, 1, 1.0, 1.04, 0.5, 0.5, 'stripout'),# corridor, last strip leaves
    ('0008', 10.4, 1, 1.1, 1.15, 0.5, 0.5, ''),        # food stall
    ('0071', 2.00, 1, 1.4, 1.4, 0.40, 0.60, ''),       # harbour boats
    ('0016', 5.00, 1, 1.2, 1.2, 0.5, 0.5, ''),         # food court
    ('0056', 3.40, 1, 1.3, 1.3, 0.5, 0.3, ''),         # night lights
    ('0087', 5.50, 1, 1.2, 1.2, 0.4, 0.6, ''),         # station
    ('0007', 3.00, 1, 1.6, 1.6, 0.95, 0.35, ''),       # 떡갈비 sign
    ('0071', 0.90, 1, 1.5, 1.55, 0.62, 0.35, ''),      # mountain
    ('0056', 0.00, 1, 1.0, 1.08, 0.5, 0.5, ''),        # finale
]
assert len(S) == len(CUTS) - 1

# grid cells: (row, col, source, t_in, appear_t, vanish_t) relative to segment start
GRID = [
    (0, 0, '0007', 7.0, 0.00, 1.62), (2, 2, '0063', 4.0, 0.08, 1.66),
    (0, 1, '0016', 3.0, 0.17, 1.58), (0, 2, '0071', 0.5, 0.25, 1.70),
    (1, 2, 'p20', 0.0, 0.33, 1.74), (2, 0, '0087', 1.0, 0.42, 1.54),
    (1, 0, '0056', 1.0, 0.50, 1.78), (2, 1, '0007', 2.5, 0.58, 1.50),
]
CENTER_IN, CENTER_OUT = 0.62, 1.70
# strips (x index 0..4 of 384 px, source, t_in, appear_t)
STRIPS = [(4, '0056', 1.0, 0.375), (3, 'p18', 0.0, 0.708), (0, '0007', 6.0, 1.04),
          (1, '0008', 11.3, 1.125)]


def src_path(src):
    return os.path.join(FOOT, src + ('.jpg' if src.startswith('p') else '.mp4'))


def inp(src, tin, dur, speed=1):
    if src.startswith('p'):
        return ['-loop', '1', '-framerate', str(FPS), '-t', f'{dur + 0.3:.3f}', '-i', src_path(src)]
    return ['-ss', f'{tin:.3f}', '-t', f'{dur * speed + 0.3:.3f}', '-i', src_path(src)]


def frame(z0, z1, px, py, n, w=W, h=H):
    """scale+crop to w x h with optional linear zoom, then grade."""
    dur = max(n / FPS, 1e-3)
    z = f"{z0}" if z0 == z1 else f"({z0}+({z1}-{z0})*min(t/{dur:.4f},1))"
    return (f"scale=w='2*trunc({w / 2}*{z}*max(1,{h}*iw/ih/{w})+0.5)':h=-2:eval=frame:flags=bicubic,"
            f"crop={w}:{h}:x='(iw-{w})*{px}':y='(ih-{h})*{py}',setsar=1,{GRADE}")


def pre(src, speed, i):
    if src.startswith('p'):
        return f"[{i}:v]fps={FPS},"
    return f"[{i}:v]setpts=(PTS-STARTPTS)/{speed},fps={FPS},"


def cmd_for(i, still=None):
    src, tin, speed, z0, z1, px, py, fx = S[i]
    n = FR[i + 1] - FR[i]
    dur = n / FPS
    out = still or os.path.join(SEG, f'{i:03d}.mp4')
    args = ['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y']
    if fx == 'white':
        args += ['-f', 'lavfi', '-i', f'color=c=0xFFFBF2:s={W}x{H}:r={FPS}']
        graph = "[0:v]format=yuv420p[out]"
    elif fx == 'grid':
        args += inp(src, tin, dur, speed)
        parts = [pre(src, speed, 0) + frame(z0, z1, px, py, n) + ",split[bg][cm]",
                 "[cm]scale=640:360[center]"]
        last = 'bg'
        for k, (r, c, s2, t2, a, b) in enumerate(GRID):
            args += inp(s2, t2, dur)
            parts.append(pre(s2, 1, k + 1) + frame(1.15, 1.15, 0.5, 0.5, n, 640, 360) + f"[c{k}]")
            parts.append(f"[{last}][c{k}]overlay=x={c * 640}:y={r * 360}:"
                         f"enable='between(t,{a},{b})'[o{k}]")
            last = f'o{k}'
        parts.append(f"[{last}][center]overlay=x=640:y=360:enable='between(t,{CENTER_IN},{CENTER_OUT})'[g]")
        lines = ",".join(f"drawbox=x={x}:y=0:w=4:h={H}:color=black:t=fill:enable='between(t,0,1.8)'"
                         for x in (638, 1278)) + "," + \
                ",".join(f"drawbox=x=0:y={y}:w={W}:h=4:color=black:t=fill:enable='between(t,0,1.8)'"
                         for y in (358, 718))
        parts.append(f"[g]{lines},format=yuv420p[out]")
        graph = ";".join(parts)
    elif fx == 'strips':
        args += inp(src, tin, dur, speed)
        parts = [pre(src, speed, 0) + frame(z0, z1, px, py, n) + "[bg]"]
        last = 'bg'
        for k, (xi, s2, t2, a) in enumerate(STRIPS):
            args += inp(s2, t2, dur)
            parts.append(pre(s2, 1, k + 1) + frame(1.0, 1.0, 0.5, 0.5, n, 384, H) + f"[s{k}]")
            parts.append(f"[{last}][s{k}]overlay=x={xi * 384}:y=0:enable='gte(t,{a})'[o{k}]")
            last = f'o{k}'
        parts.append(f"[{last}]format=yuv420p[out]")
        graph = ";".join(parts)
    elif fx == 'stripout':
        xi, s2, t2, a = STRIPS[0]
        t_strip = t2 + (FR[i] - FR[i - 1]) / FPS
        args += inp(src, tin, dur, speed) + inp(s2, t_strip, dur)
        graph = (pre(src, speed, 0) + frame(z0, z1, px, py, n) + "[bg];"
                 + pre(s2, 1, 1) + frame(1.0, 1.0, 0.5, 0.5, n, 384, H) + "[s];"
                 f"[bg][s]overlay=x='{xi * 384}+(t/0.17)*384':y=0:enable='lt(t,0.17)',format=yuv420p[out]")
    else:
        args += inp(src, tin, dur, speed)
        chain = pre(src, speed, 0) + frame(z0, z1, px, py, n)
        if fx == 'whip':
            chain += ",avgblur=sizeX=160:sizeY=1,eq=brightness=0.04"
        if fx == 'intro':  # box grows from 1/3 to full over 6 frames
            chain += (f",split[f][k];[k]scale=w='2*trunc(({W}/3+({W}*2/3)*min(t/0.25,1))/2)':h=-2:eval=frame[box];"
                      f"color=c=black:s={W}x{H}:r={FPS}[blk];"
                      f"[blk][box]overlay=x=(W-w)/2:y=(H-h)/2:eval=frame[intro];"
                      f"[f][intro]overlay=enable='lt(t,0.25)'")
        graph = chain + ",format=yuv420p[out]"
    args += ['-filter_complex', graph, '-map', '[out]']
    if still:
        return args + ['-ss', f'{min(dur * 0.6, dur - 0.05):.3f}', '-vf',
                       f"scale=384:216,drawtext=text='{i} {src} {fx}':x=4:y=4:fontsize=16:"
                       "fontcolor=yellow:box=1:boxcolor=black", '-frames:v', '1', out] \
            if False else args + ['-frames:v', '1', out]
    return args + ['-an', '-frames:v', str(n), '-r', str(FPS), '-c:v', 'libx264',
                   '-preset', 'fast', '-crf', '12', '-pix_fmt', 'yuv420p', out]


def run(c):
    r = subprocess.run(c, capture_output=True, text=True)
    if r.returncode:
        print('FAIL', c[-1], r.stderr[-1200:])
    return r.returncode


def frames_of(p):
    r = subprocess.run(['ffprobe', '-v', 'error', '-count_frames', '-select_streams', 'v:0',
                        '-show_entries', 'stream=nb_read_frames', '-of', 'csv=p=0', p],
                       capture_output=True, text=True)
    return int(r.stdout.strip() or 0)


INTER = '/usr/share/fonts/opentype/inter/'


def captions():
    sh = ':shadowcolor=black@0.5:shadowx=2:shadowy=2'
    en = "enable='between(t,0.25,1.55)'"
    def d(font, text, size, x, y):
        return (f"drawtext=fontfile='{INTER}{font}':text='{text}':fontsize={size}:fontcolor=white:"
                f"x={x}:y={y}:{en}{sh}")
    return ','.join([
        d('Inter-Light.otf', 'A   Trip   To', 30, 'w*0.21-tw/2', 'h*0.405'),
        d('Inter-SemiBold.otf', 'Busan', 74, 'w*0.21-tw/2', 'h*0.405+38'),
        d('Inter-Light.otf', 'Shot On DJI', 30, 'w*0.77-tw/2', 'h*0.405'),
        d('Inter-SemiBold.otf', 'Osmo Pocket 4', 74, 'w*0.77-tw/2', 'h*0.405+38'),
    ])


def main(mode):
    os.makedirs(SEG, exist_ok=True)
    if mode == 'segments':
        only = [int(x) for x in sys.argv[2:]] or range(len(S))
        with ThreadPoolExecutor(3) as ex:
            list(ex.map(run, [cmd_for(i) for i in only]))
        bad = [(i, FR[i + 1] - FR[i], frames_of(os.path.join(SEG, f'{i:03d}.mp4')))
               for i in range(len(S))]
        print('frame mismatches:', [b for b in bad if b[1] != b[2]])
    elif mode == 'final':
        lst = os.path.join(OUT, 'list.txt')
        with open(lst, 'w') as f:
            for i in range(len(S)):
                f.write(f"file '{os.path.join(SEG, f'{i:03d}.mp4')}'\n")
        out = os.path.join(OUT, 'busan_style3.mp4')
        vfx = f"vignette=angle=PI/5,{captions()},noise=alls=3:allf=t,format=yuv420p"
        run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y',
             '-f', 'concat', '-safe', '0', '-i', lst, '-i', REEL,
             '-map', '0:v', '-map', '1:a', '-vf', vfx,
             '-af', f"afade=t=out:st={TOTAL - 0.3:.2f}:d=0.3",
             '-c:v', 'libx264', '-preset', 'slow', '-b:v', '8M', '-maxrate', '10M',
             '-bufsize', '16M', '-x264-params', 'aq-mode=3', '-profile:v', 'high',
             '-level', '4.1', '-pix_fmt', 'yuv420p', '-r', str(FPS),
             '-c:a', 'aac', '-b:a', '192k', '-ar', '48000',
             '-movflags', '+faststart', '-t', f'{TOTAL:.3f}', out])
        print(out)


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else 'segments')
