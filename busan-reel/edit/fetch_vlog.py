#!/usr/bin/env python3
"""Download every Busan source clip from Google Drive one at a time and keep only
a 1080p proxy (H.264, original audio), deleting the 4K original right after.

Usage: fetch_vlog.py            -> proxies in ../proxy/NNNN.mp4, photos in ../footage/pNN.jpg
Sources: vlog_sources.json (file name -> Drive file id; files must be link-viewable).
"""
import os, sys, json, subprocess, threading, queue

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
PROXY = os.path.join(ROOT, 'proxy')
FOOT = os.path.join(ROOT, 'footage')
TMP = os.path.join(ROOT, 'dl')
URL = 'https://drive.usercontent.google.com/download?id={}&export=download&confirm=t'


def num(name):
    return name.split('_')[2]


def transcode(src, dst):
    # 4K/10-bit HEVC -> 1080p 8-bit H.264 proxy; the vertical 0088 keeps its aspect (1080 wide).
    vf = "scale='if(gt(iw,ih),1920,1080)':-2:flags=lanczos,format=yuv420p"
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', src, '-vf', vf,
                    '-c:v', 'libx264', '-preset', 'faster', '-crf', '17',
                    '-c:a', 'aac', '-b:a', '192k', '-movflags', '+faststart',
                    dst + '.part.mp4'], check=True)
    os.replace(dst + '.part.mp4', dst)


def main():
    os.makedirs(PROXY, exist_ok=True); os.makedirs(FOOT, exist_ok=True); os.makedirs(TMP, exist_ok=True)
    src = json.load(open(os.path.join(HERE, 'vlog_sources.json')))
    q = queue.Queue(maxsize=2)  # at most 2 originals on disk waiting

    def worker():
        while True:
            item = q.get()
            if item is None:
                return
            raw, dst = item
            try:
                transcode(raw, dst); print('proxy', os.path.basename(dst), flush=True)
            except subprocess.CalledProcessError as e:
                print('FAIL', dst, e, flush=True)
            finally:
                os.remove(raw)

    ws = [threading.Thread(target=worker) for _ in range(2)]
    for w in ws: w.start()
    for name, fid in src.items():
        n = num(name)
        if name.upper().endswith('.JPG'):
            dst = os.path.join(FOOT, 'p%s.jpg' % n[-2:])
            if not os.path.exists(dst):
                subprocess.run(['curl', '-sSL', '-o', dst, URL.format(fid)], check=True)
            continue
        dst = os.path.join(PROXY, n + '.mp4')
        if os.path.exists(dst):
            continue
        raw = os.path.join(TMP, n + '.MP4')
        subprocess.run(['curl', '-sSL', '--retry', '4', '-o', raw, URL.format(fid)], check=True)
        print('downloaded', n, os.path.getsize(raw) // 2**20, 'MB', flush=True)
        q.put((raw, dst))
    for _ in ws: q.put(None)
    for w in ws: w.join()


if __name__ == '__main__':
    main()
