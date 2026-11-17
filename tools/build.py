import subprocess, json, os, sys, numpy as np, wave
from PIL import Image, ImageDraw, ImageFont
A='/home/claude/balloon-1/assets'; B='/home/claude/ss/build'; W,H=1080,1920; FPS=30
sys.path.insert(0,'/home/claude/ss'); import music
def dur(p): return float(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration','-of','csv=p=0',p]).decode())
def font(sz,w=700):
    f=ImageFont.truetype(f'{A}/Fredoka.ttf',sz)
    try: f.set_variation_by_axes([w,100])
    except Exception:
        try: f.set_variation_by_name('Bold')
        except Exception: pass
    return f
def text_png(path,lines):
    im=Image.new('RGBA',(W,H),(0,0,0,0)); d=ImageDraw.Draw(im)
    for (txt,sz,y,fill,stroke,sw) in lines:
        f=font(sz); bb=d.textbbox((0,0),txt,font=f,stroke_width=sw); w=bb[2]-bb[0]
        x=(W-w)//2-bb[0]
        d.text((x+8,y+10),txt,font=f,fill=(0,0,0,70),stroke_width=sw,stroke_fill=(0,0,0,70))
        d.text((x,y),txt,font=f,fill=fill,stroke_width=sw,stroke_fill=stroke)
    im.save(path)
COLORS=[((255,92,92),(255,255,255)),((40,150,240),(255,255,255)),((40,190,120),(255,255,255)),((255,150,30),(255,255,255))]
def scene(img,out,d,mode='portrait'):
    n=int(d*FPS)
    if mode=='portrait':
        vf=(f"scale=2160:-2,crop=2160:3840,zoompan=z='1+0.0009*on':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={n}:s={W}x{H}:fps={FPS}")
        subprocess.run(['ffmpeg','-y','-v','error','-loop','1','-i',img,'-vf',vf,'-frames:v',str(n),'-pix_fmt','yuv420p','-c:v','libx264','-preset','veryfast','-crf','20',out],check=True)
    else:
        subprocess.run(['ffmpeg','-y','-v','error','-loop','1','-i',img,'-vf',f"scale={W}:{H},zoompan=z='1+0.0006*on':d={n}:s={W}x{H}:fps={FPS}",'-frames:v',str(n),'-pix_fmt','yuv420p','-c:v','libx264','-preset','veryfast','-crf','20',out],check=True)
def overlay(base,png,out,start=0.25):
    subprocess.run(['ffmpeg','-y','-v','error','-i',base,'-loop','1','-i',png,'-filter_complex',
        f"[1:v]format=rgba,fade=t=in:st={start}:d=0.35:alpha=1[t];[0:v][t]overlay=0:0:shortest=1,format=yuv420p",
        '-c:v','libx264','-preset','veryfast','-crf','20',out],check=True)
def card(bgimg,out,title_lines,img_w=None,circle=False):
    im=Image.new('RGB',(W,H),(110,195,255)); d=ImageDraw.Draw(im)
    for y in range(H):
        t=y/H; c=(int(120+90*t),int(200+40*t),int(255-20*t)); d.line([(0,y),(W,y)],fill=c)
    src=Image.open(bgimg).convert('RGB')
    if img_w: src=src.resize((img_w,int(src.height*img_w/src.width)))
    x=(W-src.width)//2; y=(H-src.height)//2+120
    mask=Image.new('L',src.size,0)
    if circle: ImageDraw.Draw(mask).ellipse([6,6,src.width-6,src.height-6],fill=255)
    else: ImageDraw.Draw(mask).rounded_rectangle([0,0,src.width,src.height],radius=60,fill=255)
    im.paste(src,(x,y),mask); im.save(out)
def build(ep, letters, words, intro_title, outro_title):
    segs=[]; voices=[]; t=0.0
    # intro
    iv=f'{A}/intro{ep}.mp3'; d=max(dur(iv)+1.0,3.5)
    card(f'{A}/avatar.png',f'{B}/introbg{ep}.png',None,img_w=860,circle=True)
    scene(f'{B}/introbg{ep}.png',f'{B}/s_intro{ep}.mp4',d,mode='full')
    text_png(f'{B}/t_intro{ep}.png',[(intro_title[0],120,170,(255,255,255),(30,42,74),12),(intro_title[1],150,330,(255,201,60),(30,42,74),14)])
    overlay(f'{B}/s_intro{ep}.mp4',f'{B}/t_intro{ep}.png',f'{B}/o_intro{ep}.mp4',0.1)
    segs.append(f'{B}/o_intro{ep}.mp4'); voices.append((iv,t+0.3)); t+=d
    for i,(L,wd) in enumerate(zip(letters,words)):
        v=f'{A}/v{L}.mp3'; d=max(dur(v)+1.2,4.0)
        scene(f'{A}/{L}.png',f'{B}/s_{L}.mp4',d)
        col,st=COLORS[i%4]
        text_png(f'{B}/t_{L}.png',[(f'{L} {L.lower()}',330,90,col,(255,255,255),18),(wd,140,470,(255,255,255),(30,42,74),12)])
        overlay(f'{B}/s_{L}.mp4',f'{B}/t_{L}.png',f'{B}/o_{L}.mp4',0.15)
        segs.append(f'{B}/o_{L}.mp4'); voices.append((v,t+0.35)); t+=d
    ov=f'{A}/outro{ep}.mp3'; d=max(dur(ov)+1.6,4.0)
    card(f'{A}/lineup.png',f'{B}/outrobg{ep}.png',None,img_w=1020)
    scene(f'{B}/outrobg{ep}.png',f'{B}/s_outro{ep}.mp4',d,mode='full')
    text_png(f'{B}/t_outro{ep}.png',[(outro_title[0],110,250,(255,255,255),(30,42,74),12),(' '.join(letters),170,420,(255,92,92),(255,255,255),16),('Singing Street',110,1450,(255,255,255),(30,42,74),12)])
    overlay(f'{B}/s_outro{ep}.mp4',f'{B}/t_outro{ep}.png',f'{B}/o_outro{ep}.mp4',0.1)
    segs.append(f'{B}/o_outro{ep}.mp4'); voices.append((ov,t+0.3)); t+=d
    open(f'{B}/list{ep}.txt','w').write(''.join(f"file '{s}'\n" for s in segs))
    subprocess.run(['ffmpeg','-y','-v','error','-f','concat','-safe','0','-i',f'{B}/list{ep}.txt','-c','copy',f'{B}/video{ep}.mp4'],check=True)
    total=dur(f'{B}/video{ep}.mp4')
    # audio mix
    music.make(total,out=f'{B}/bed{ep}.wav',seed=ep)
    SR=44100
    def load(p):
        raw=subprocess.check_output(['ffmpeg','-v','error','-i',p,'-f','s16le','-ac','1','-ar',str(SR),'-'])
        return np.frombuffer(raw,np.int16).astype(np.float32)/32768
    bed=load(f'{B}/bed{ep}.wav'); mix=np.zeros(int(total*SR)+SR); vtrack=np.zeros_like(mix)
    for p,st in voices:
        v=load(p); s=int(st*SR); vtrack[s:s+len(v)]+=v[:len(vtrack)-s]
    # duck music under voice
    envv=np.convolve(np.abs(vtrack),np.ones(4410)/4410,mode='same'); duck=np.where(envv>0.01,0.35,0.6)
    duck=np.convolve(duck,np.ones(8820)/8820,mode='same')
    mix[:len(bed)]+=bed*duck[:len(bed)]; mix+=vtrack*1.15
    mix=mix[:int(total*SR)]; mix/=max(1.0,np.max(np.abs(mix))/0.95)
    w=wave.open(f'{B}/mix{ep}.wav','wb'); w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((mix*32767).astype(np.int16).tobytes()); w.close()
    final=f'{B}/singing_street_ep{ep}.mp4'
    subprocess.run(['ffmpeg','-y','-v','error','-i',f'{B}/video{ep}.mp4','-i',f'{B}/mix{ep}.wav','-c:v','copy','-c:a','aac','-b:a','192k','-shortest','-movflags','+faststart',final],check=True)
    print(ep, round(total,2), os.path.getsize(final))
if __name__=='__main__':
    which=sys.argv[1]
    if which=='1': build(1,list('ABCD'),['Apple','Ball','Cat','Duck'],('Let\'s learn','A B C D!'),('Yay! You know',))
    if which=='2': build(2,list('EFGH'),['Egg','Fish','Grapes','Hat'],('Let\'s learn','E F G H!'),('Hooray! You know',))
