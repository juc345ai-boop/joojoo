#!/usr/bin/env python3
"""Busan edit #4: follows the fourth reference reel (rapid POV vlog montage,
muted olive-teal grade, white-border snapshot frames, pillarboxed verticals,
silhouette flash, whip streaks, VLOG caption), 25 fps, 17.48 s.

Usage: render4.py [segments|final]
"""
import os, sys, subprocess
from concurrent.futures import ThreadPoolExecutor

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FOOT = os.path.join(ROOT, 'footage')
REEL = os.path.join(ROOT, 'reel4', 'reel.mp4')
OUT = os.path.join(ROOT, 'edit4')
SEG = os.path.join(OUT, 'segs')
FPS = 25
TOTAL = 17.48
W, H = 1920, 1080

GRADE = ("eq=saturation=0.72:gamma=0.82:contrast=1.12,"
         "curves=r='0/0 0.5/0.47 1/0.95':g='0/0.02 0.5/0.5 1/0.96':b='0/0.045 0.5/0.47 1/0.9',"
         "colorbalance=rs=-0.03:gs=0.01:bs=0.03:gm=0.025:rh=0.02:bh=-0.02")

CUTS = [0.00, 0.16, 0.32, 0.48, 0.64, 1.12, 1.56, 2.00, 2.20, 2.40, 2.60, 2.96,
        3.36, 3.68, 4.00, 4.24, 4.68, 5.16, 5.88, 6.00, 6.12, 6.36, 6.88, 7.12,
        7.40, 7.72, 8.24, 8.80, 9.08, 9.24, 9.44, 9.80, 10.56, 10.88, 11.16,
        11.40, 11.56, 12.48, 12.80, 13.72, 14.36, 14.52, 14.92, 15.20, 15.48,
        15.76, 16.04, 16.48, 16.72, TOTAL]
FR = [round(c * FPS) for c in CUTS]

# (source, t_in, zoom_start, zoom_end, pan_x, pan_y, fx)
# fx: '' | 'frame' (white snapshot border) | 'pillar' (vertical, pillarboxed)
#     | 'sil' (silhouette white-out mid shot) | 'whip'
S = [
    ('0071', 0.00, 1.3, 1.35, 0.60, 0.40, ''),     # hill city
    ('0071', 4.60, 1.1, 1.1, 0.5, 0.3, ''),        # buildings
    ('0087', 2.00, 1.4, 1.4, 0.5, 0.10, ''),       # station ceiling
    ('0007', 1.00, 1.0, 1.0, 0.5, 0.5, ''),        # market entrance
    ('p20',  0.00, 1.2, 1.28, 0.5, 0.4, ''),       # table POV
    ('0071', 2.40, 1.1, 1.15, 0.5, 0.6, ''),       # harbour railing
    ('0008', 1.00, 1.3, 1.3, 0.5, 0.10, ''),       # signs overhead
    ('0088', 3.00, 1.0, 1.0, 0.5, 0.45, ''),       # room
    ('0088', 6.00, 1.0, 1.0, 0.5, 0.60, ''),
    ('0088', 8.00, 1.0, 1.0, 0.5, 0.75, ''),
    ('0063', 4.00, 1.0, 1.0, 0.5, 0.5, ''),        # bus streaks
    ('0087', 0.50, 1.0, 1.05, 0.5, 0.5, ''),       # station hall
    ('0008', 11.5, 1.6, 1.6, 0.90, 0.85, ''),      # food
    ('p20',  0.00, 1.0, 1.04, 0.5, 0.5, ''),       # table
    ('0008', 6.50, 1.2, 1.2, 0.5, 0.45, ''),       # woman walking
    ('0071', 3.60, 1.0, 1.0, 0.5, 0.5, 'sil'),     # street + silhouette flash
    ('0008', 9.00, 1.3, 1.3, 0.30, 0.5, ''),
    ('0008', 12.0, 1.3, 1.3, 0.5, 0.6, ''),        # stall food
    ('0016', 3.00, 1.0, 1.0, 0.5, 0.5, 'frame'),   # snapshot frames x3
    ('0007', 7.00, 1.0, 1.0, 0.5, 0.5, 'frame'),
    ('0087', 6.00, 1.0, 1.0, 0.5, 0.5, 'frame'),
    ('0016', 5.50, 1.1, 1.1, 0.5, 0.5, ''),        # food court
    ('0071', 5.50, 1.4, 1.4, 0.5, 0.0, ''),        # building up
    ('0071', 3.90, 1.0, 1.0, 0.5, 0.5, ''),        # street pan
    ('0007', 13.0, 1.0, 1.0, 0.5, 0.5, ''),        # corridor
    ('0071', 0.60, 1.0, 1.04, 0.5, 0.5, ''),       # harbour wide
    ('0007', 15.0, 1.8, 1.8, 0.5, 1.0, ''),        # floor POV
    ('0008', 15.5, 1.1, 1.1, 0.5, 0.5, ''),        # crowd
    ('0016', 1.00, 2.6, 2.6, 0.62, 0.33, ''),      # 돼지국밥 sign
    ('0087', 2.20, 2.4, 2.4, 0.55, 0.20, ''),      # departure board
    ('0071', 1.00, 1.2, 1.2, 0.5, 0.5, ''),
    ('0007', 10.5, 1.0, 1.04, 0.5, 0.5, ''),       # corridor walk
    ('p18',  0.00, 1.0, 1.0, 0.5, 0.5, 'pillar'), # vertical photos, pillarboxed
    ('p19',  0.00, 1.0, 1.0, 0.5, 0.5, 'pillar'),
    ('0008', 13.0, 1.1, 1.1, 0.5, 0.5, ''),
    ('0001', 1.00, 1.6, 1.6, 0.5, 0.3, ''),        # ceiling TV
    ('0056', 0.00, 1.0, 1.04, 0.5, 0.5, ''),       # NIGHT: stairs
    ('0056', 2.00, 1.3, 1.3, 0.5, 0.5, ''),
    ('0063', 0.00, 1.0, 1.04, 0.5, 0.5, ''),       # window night
    ('0063', 5.00, 1.0, 1.0, 0.5, 0.5, ''),
    ('0056', 4.50, 1.2, 1.2, 0.5, 0.4, 'whip'),    # light streak
    ('0063', 2.00, 1.1, 1.1, 0.5, 0.5, ''),
    ('0056', 3.50, 1.5, 1.5, 0.5, 0.20, ''),
    ('0056', 1.20, 1.2, 1.2, 0.5, 0.5, ''),
    ('0056', 4.00, 1.8, 1.8, 0.30, 0.10, ''),
    ('p20',  0.00, 1.6, 1.6, 0.85, 0.70, ''),      # cups
    ('0063', 3.20, 1.8, 1.8, 0.5, 0.3, ''),        # window lights
    ('0063', 4.60, 1.0, 1.0, 0.5, 0.5, ''),
    ('0056', 5.20, 1.0, 1.05, 0.5, 0.5, ''),       # last shot
]
assert len(S) == len(CUTS) - 1, (len(S), len(CUTS))


def src_path(src):
    return os.path.join(FOOT, src + ('.jpg' if src.startswith('p') else '.mp4'))


def cmd_for(i):
    src, tin, z0, z1, px, py, fx = S[i]
    n = FR[i + 1] - FR[i]
    dur = n / FPS
    if src.startswith('p'):
        inp = ['-loop', '1', '-framerate', str(FPS), '-t', f'{dur + 0.3:.3f}', '-i', src_path(src)]
        head = f"[0:v]fps={FPS},"
    else:
        inp = ['-ss', f'{tin:.3f}', '-t', f'{dur + 0.3:.3f}', '-i', src_path(src)]
        head = f"[0:v]setpts=PTS-STARTPTS,fps={FPS},"
    z = f"{z0}" if z0 == z1 else f"({z0}+({z1}-{z0})*min(t/{dur:.4f},1))"
    if fx == 'pillar':  # fit height, black bars left/right
        body = (f"scale=w=-2:h='2*trunc({H / 2}*{z}+0.5)':eval=frame:flags=bicubic,"
                f"crop='min(iw,{W})':{H}:(iw-ow)/2:(ih-{H})/2,{GRADE},"
                f"pad={W}:{H}:(ow-iw)/2:0:black")
    else:
        body = (f"scale=w='2*trunc({W / 2}*{z}*max(1,{H}*iw/ih/{W})+0.5)':h=-2:eval=frame:flags=bicubic,"
                f"crop={W}:{H}:x='(iw-{W})*{px}':y='(ih-{H})*{py}',setsar=1,{GRADE}")
    if fx == 'frame':
        body += (",scale=1840:1036,pad=1920:1080:40:22:black,"
                 "drawbox=x=32:y=14:w=1856:h=1052:color=white:t=7")
    if fx == 'sil':  # silhouette white-out for 3 frames in the middle of the shot
        body += (",split[a][b];[b]hue=s=0,curves=all='0/0 0.16/0.04 0.30/1 1/1'[w];"
                 "[a][w]overlay=enable='between(n,5,7)'")
    if fx == 'whip':
        body += ",avgblur=sizeX=160:sizeY=1,eq=brightness=0.05:saturation=1.3"
    graph = head + body + ",setsar=1,format=yuv420p[out]"
    return (['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y'] + inp +
            ['-filter_complex', graph, '-map', '[out]', '-an', '-frames:v', str(n),
             '-r', str(FPS), '-c:v', 'libx264', '-preset', 'fast', '-crf', '12',
             '-pix_fmt', 'yuv420p', os.path.join(SEG, f'{i:03d}.mp4')])


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


def captions():
    f = '/usr/share/fonts/opentype/inter/Inter-Bold.otf'
    common = f"fontfile='{f}':fontsize=50:fontcolor=white@0.95:y=h*0.53:enable='between(t,0,2.6)'"
    return (f"drawtext={common}:text='<<VLOG_01':x=w*0.085,"
            f"drawtext={common}:text='BUSAN>>':x=w*0.915-tw")


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
        with open(lst, 'w') as fh:
            for i in range(len(S)):
                fh.write(f"file '{os.path.join(SEG, f'{i:03d}.mp4')}'\n")
        out = os.path.join(OUT, 'busan_style4.mp4')
        vfx = (f"vignette=angle=PI/5,{captions()},noise=alls=3:allf=t,"
               f"fade=t=out:st={TOTAL - 0.5:.2f}:d=0.5,format=yuv420p")
        run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y',
             '-f', 'concat', '-safe', '0', '-i', lst, '-i', REEL,
             '-map', '0:v', '-map', '1:a', '-vf', vfx,
             '-af', f"afade=t=out:st={TOTAL - 0.4:.2f}:d=0.4",
             '-c:v', 'libx264', '-preset', 'slow', '-b:v', '8M', '-maxrate', '10M',
             '-bufsize', '16M', '-x264-params', 'aq-mode=3', '-profile:v', 'high',
             '-level', '4.1', '-pix_fmt', 'yuv420p', '-r', str(FPS),
             '-c:a', 'aac', '-b:a', '192k', '-ar', '48000',
             '-movflags', '+faststart', '-t', f'{TOTAL:.3f}', out])
        print(out)


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else 'segments')
