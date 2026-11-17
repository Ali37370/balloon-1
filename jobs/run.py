import os
os.makedirs('assets', exist_ok=True)
import json, os, subprocess, urllib.request, glob, sys
log=open('assets/log.txt','a')
def P(*a):
    print(*a); print(*a, file=log); log.flush()
for f in sorted(glob.glob('jobs/*.json')):
    job = json.load(open(f))
    for it in job.get('images', []):
        out = os.path.join('assets', it['name'])
        if os.path.exists(out): continue
        try:
            req = urllib.request.Request(it['url'], headers={'User-Agent': 'Mozilla/5.0'})
            data = urllib.request.urlopen(req, timeout=120).read()
            open(out, 'wb').write(data); P('img ok', out, len(data))
        except Exception as e: P('img fail', out, e)
    for it in job.get('tts', []):
        out = os.path.join('assets', it['name'])
        if os.path.exists(out): continue
        cmd = ['edge-tts', '--voice', it.get('voice', 'en-US-AnaNeural'), '--rate='+it.get('rate', '-5%'), '--pitch='+it.get('pitch', '+0Hz'), '--text', it['text'], '--write-media', out]
        r = subprocess.run(cmd, capture_output=True, text=True); P('tts', out, r.returncode, r.stderr[-300:])
        if r.returncode != 0 or not os.path.exists(out) or os.path.getsize(out) == 0:
            try:
                from gtts import gTTS
                gTTS(it['text'], lang='en', tld='us').save(out); P('gtts ok', out)
            except Exception as e: P('gtts fail', out, e)
