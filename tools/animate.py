import numpy as np, subprocess, math, random, sys, wave, os
from PIL import Image, ImageDraw, ImageFont, ImageFilter
sys.path.insert(0,'/home/claude/ss'); import music
A='/home/claude/balloon-1/assets'; S='/home/claude/ss'; W,H=1080,1920; FPS=30; BPM=116; BEAT=60/BPM
def font(sz,w=700):
    f=ImageFont.truetype(f'{A}/Fredoka.ttf',sz); f.set_variation_by_axes([w,100]); return f
def text_img(txt,sz,fill,stroke=(255,255,255),sw=16,shadow=True):
    f=font(sz); d=ImageDraw.Draw(Image.new('RGBA',(1,1)))
    bb=d.textbbox((0,0),txt,font=f,stroke_width=sw); w,h=bb[2]-bb[0]+30,bb[3]-bb[1]+30
    im=Image.new('RGBA',(w,h),(0,0,0,0)); dd=ImageDraw.Draw(im)
    if shadow: dd.text((15-bb[0]+6,15-bb[1]+9),txt,font=f,fill=(0,0,0,80),stroke_width=sw,stroke_fill=(0,0,0,80))
    dd.text((15-bb[0],15-bb[1]),txt,font=f,fill=fill,stroke_width=sw,stroke_fill=stroke); return im
def ease_back(t):  # overshoot 0..1
    t=min(max(t,0),1); c=1.9; return 1+(c+1)*(t-1)**3+c*(t-1)**2
def elastic(t):
    t=min(max(t,0),1)
    if t in (0,1): return t
    return 2**(-10*t)*math.sin((t*10-0.75)*2*math.pi/3)+1
def place(canvas,im,cx,by,scale=1.0,rot=0,alpha=1.0,sx=1.0,sy=1.0):
    if scale<=0.01 or alpha<=0.01: return
    w=max(1,int(im.width*scale*sx)); h=max(1,int(im.height*scale*sy))
    t=im.resize((w,h),Image.BILINEAR)
    if rot: t=t.rotate(rot,resample=Image.BILINEAR,expand=True)
    if alpha<1:
        a=t.getchannel('A').point(lambda v:int(v*alpha)); t.putalpha(a)
    canvas.alpha_composite(t,(int(cx-t.width/2),int(by-t.height)))
def shadow_ell(canvas,cx,by,wid,strength=0.35):
    sh=Image.new('RGBA',(int(wid),int(wid*0.22)),(0,0,0,0)); d=ImageDraw.Draw(sh)
    d.ellipse([0,0,sh.width-1,sh.height-1],fill=(40,40,60,int(255*strength))); sh=sh.filter(ImageFilter.GaussianBlur(10))
    canvas.alpha_composite(sh,(int(cx-sh.width/2),int(by-sh.height/2)))
COLS=[(255,92,92),(40,150,240),(40,190,120),(255,150,30),(150,100,255)]
NOTE_COL=[(255,92,92),(255,201,60),(40,150,240),(40,190,120),(150,100,255)]
def note_img(c,sz=70):
    im=Image.new('RGBA',(sz,int(sz*1.3)),(0,0,0,0)); d=ImageDraw.Draw(im)
    d.ellipse([0,int(sz*0.8),int(sz*0.55),int(sz*1.25)],fill=c+(255,)); d.rectangle([int(sz*0.45),0,int(sz*0.55),int(sz*1.05)],fill=c+(255,))
    d.polygon([(int(sz*0.55),0),(sz,int(sz*0.25)),(int(sz*0.55),int(sz*0.35))],fill=c+(255,)); return im
NOTES=[note_img(c) for c in NOTE_COL]
def star_img(c,sz=40):
    im=Image.new('RGBA',(sz,sz),(0,0,0,0)); d=ImageDraw.Draw(im); r=sz/2
    pts=[(r+r*math.cos(math.pi/2+i*math.pi/5)*(1 if i%2==0 else 0.45), r-r*math.sin(math.pi/2+i*math.pi/5)*(1 if i%2==0 else 0.45)) for i in range(10)]
    d.polygon(pts,fill=c+(255,)); return im
STARS=[star_img(c) for c in NOTE_COL+[(255,255,255)]]
def build(ep, letters, words, voices3, intro_title, outro_title, outname, party_letters=None):
    bg=Image.open(f'{A}/bg_street.png').convert('RGBA'); sc=max(W/bg.width,H/bg.height)*1.08
    bg=bg.resize((int(bg.width*sc),int(bg.height*sc)),Image.LANCZOS)
    group=Image.open(f'{A}/group_cut.png').convert('RGBA'); group=group.crop(group.getbbox())
    gs=1000/group.width; group=group.resize((1000,int(group.height*gs)),Image.LANCZOS)
    SCENE=set(L for L in letters if L in 'ABCDEFGH')
    chars={L:Image.open(f'{S}/cut_{L}.png').convert('RGBA') for L in set(list(letters)+list(party_letters or letters)) if L not in SCENE or L in (party_letters or '')}
    scenes={}
    for L in SCENE:
        im=Image.open(f'{A}/{L}.png').convert('RGBA'); sc_=max(W/im.width,H/im.height)*1.12
        scenes[L]=im.resize((int(im.width*sc_),int(im.height*sc_)),Image.LANCZOS)
    for L in chars:
        im=chars[L]; s=880/im.height; chars[L]=im.resize((int(im.width*s),880),Image.LANCZOS)
    letter_imgs={L:text_img(f'{L} {L.lower()}',330,COLS[i%5],(255,255,255),20) for i,L in enumerate(letters)}
    word_imgs={L:text_img(wd,150,(255,255,255),(30,42,74),14) for L,wd in zip(letters,words)}
    t1=text_img(intro_title[0],120,(255,255,255),(30,42,74),12); t2=[text_img(L,190 if len(letters)<=4 else 120,COLS[i%5],(255,255,255),16) for i,L in enumerate(letters)]
    o1=text_img(outro_title,120,(255,255,255),(30,42,74),12); o3=text_img('Singing Street',120,(255,255,255),(30,42,74),12)
    INTRO=8; SEG=12; OUT=10
    def rowpos(i,dy=0):
        n=len(letters)
        if n<=4: return (W/2+(i-(n-1)/2)*220, 600+dy)
        per=7; r=i//per; c=i%per; m=min(per,n-r*per)
        return (W/2+(c-(m-1)/2)*140, 520+r*150+dy)
    row=[]
    for L in (party_letters or letters):
        im=chars[L]; s_=560/im.height; row.append(im.resize((int(im.width*s_),560),Image.LANCZOS))
    def party(frame,t,b,g):
        n=len(row); xs=[W/2+(i-(n-1)/2)*265 for i in range(n)]
        order=[1,3,0,2] if n==4 else list(range(n))
        for i in order:
            ph=(b+ (0.5 if i%2 else 0))
            hop=abs(math.sin(math.pi*ph))*50 if b>1.2 else 0
            y=1760-(i%2)*70
            shadow_ell(frame,xs[i],y-8,row[i].width*0.7,0.3)
            place(frame,row[i],xs[i],y+(1-g)*1000-hop,1.0,math.sin(t*math.pi/BEAT+i)*4)
    nbeats=INTRO+SEG*len(letters)+OUT; total=nbeats*BEAT; N=int(total*FPS)
    rnd=random.Random(ep)
    parts=[dict(x=rnd.uniform(0,W),y=rnd.uniform(0,H),vy=rnd.uniform(-60,-25),ph=rnd.uniform(0,6.28),k=rnd.randrange(5),s=rnd.uniform(0.6,1.1)) for _ in range(10)]
    bursts=[]
    for i in range(len(letters)):
        b0=(INTRO+SEG*i+8)*BEAT; bursts.append(b0); bursts.append((INTRO+SEG*i)*BEAT+0.05)
    conf=[]
    for b0 in bursts:
        for _ in range(26):
            ang=rnd.uniform(0,2*math.pi); sp=rnd.uniform(400,1100)
            conf.append(dict(t0=b0,x=W/2,y=820,vx=math.cos(ang)*sp,vy=math.sin(ang)*sp-500,k=rnd.randrange(6),r=rnd.uniform(0,360),vr=rnd.uniform(-400,400)))
    ff=subprocess.Popen(['ffmpeg','-y','-v','error','-f','rawvideo','-pix_fmt','rgba','-s',f'{W}x{H}','-r',str(FPS),'-i','-','-c:v','libx264','-preset','veryfast','-crf','20','-pix_fmt','yuv420p',f'{S}/anim_v{ep}.mp4'],stdin=subprocess.PIPE)
    for f in range(N):
        t=f/FPS; b=t/BEAT; bi=int(b); bf=b-bi
        pulse=math.exp(-bf*5)  # on-beat pulse
        frame=Image.new('RGBA',(W,H))
        zx=(bg.width-W)/2+math.sin(t*0.35)*18; zy=(bg.height-H)/2+math.cos(t*0.27)*12
        frame.alpha_composite(bg,(-int(zx),-int(zy)))
        # floating notes
        for p in parts:
            y=(p['y']+p['vy']*t)%(H+200)-100; x=p['x']+math.sin(t*1.3+p['ph'])*40
            if y<1000: place(frame,NOTES[p['k']],x,y,p['s']*(1+0.15*pulse),math.sin(t*2+p['ph'])*15,0.85)
        if b<INTRO:
            gb=(b-0.5)/1.5; g=ease_back(gb) if gb>0 else 0
            hop=abs(math.sin(math.pi*b))*40 if b>2 else 0
            if g>0: party(frame,t,b,g)
            place(frame,t1,W/2,330,ease_back(b/1.0))
            for i,L in enumerate(letters):
                k=(b-2-i*(1.0 if len(letters)<=4 else 0.2))/0.6
                if k>0: place(frame,t2[i],*rowpos(i),ease_back(k)*(1+0.1*pulse))
        elif b<INTRO+SEG*len(letters):
            si=int((b-INTRO)//SEG); L=letters[si]; lb=(b-INTRO)-si*SEG
            # letter drop
            lp=elastic(lb/1.2); ly=-200+(560+200)*lp
            ls=(1+0.08*pulse) if lb>1 else 1
            if lb>11: ls*=max(0,1-(lb-11)/0.8)
            place(frame,letter_imgs[L],W/2,ly,ls,math.sin(t*3)*3)
            # word
            if lb>=4:
                ws=ease_back((lb-4)/0.6)*(1+0.06*pulse)
                if lb>11: ws*=max(0,1-(lb-11)/0.8)
                place(frame,word_imgs[L],W/2,800,ws)
            if L in SCENE:
                sc_img=scenes[L]; z=1+0.025*pulse+0.01*math.sin(t*1.5)
                sw_=int(sc_img.width*z); sh_=int(sc_img.height*z)
                im2=sc_img.resize((sw_,sh_),Image.BILINEAR)
                ox=(sw_-W)/2+math.sin(t*1.1)*14; oy=(sh_-H)/2+math.cos(t*0.9)*10
                k_in=min(1,lb/0.5); 
                frame.alpha_composite(im2,(-int(ox),-int(oy)))
                if lb<0.5:
                    wipe=Image.new('RGBA',(W,H),(255,255,255,int(255*(1-k_in)))); frame.alpha_composite(wipe)
                place(frame,letter_imgs[L],W/2,ly,ls,math.sin(t*3)*3)
                if lb>=4: place(frame,word_imgs[L],W/2,800,ws)
            # character
            if L not in SCENE:
                ch=chars[L]; side=-1 if si%2==0 else 1
                if lb<1: cx=W/2+side*900; cy=1780
                elif lb<2.2:
                    k=(lb-1)/1.2; cx=W/2+side*900*(1-ease_back(k)); cy=1780-math.sin(min(k,1)*math.pi)*260
                elif lb<11:
                    cx=W/2+math.sin(t*2.2)*30; cy=1780
                else:
                    k=(lb-11)/1.0; cx=W/2-side*1000*k**2; cy=1780-math.sin(min(k,1)*math.pi)*220
                hop=0; sq=1
                if 2.2<=lb<11:
                    hop=abs(math.sin(math.pi*lb))*55*(1.6 if 8<=lb<10 else 1)
                    sq=1-0.06*math.exp(-((lb%1))*8)
                rot=math.sin(t*math.pi/BEAT)*5 if 2.2<=lb<11 else 0
                if 8<=lb<9: rot+= (lb-8)*360*0  # keep upright
                shadow_ell(frame,cx,cy-10,ch.width*0.75*(1-hop/300),0.32)
                place(frame,ch,cx,cy-hop,1.0,rot,1,1/sq**0.5,sq)
                if lb>=4: place(frame,word_imgs[L],W/2,800,ws)
        else:
            ob=b-(INTRO+SEG*len(letters))
            g=ease_back(ob/1.2); hop=abs(math.sin(math.pi*ob))*60 if ob>1.2 else 0
            party(frame,t,ob,g)
            place(frame,o1,W/2,300,ease_back(ob/0.8))
            for i,L in enumerate(letters):
                k=(ob-1-i*(0.5 if len(letters)<=4 else 0.1))/0.5
                if k>0: place(frame,t2[i],*rowpos(i,-40),ease_back(k)*(1+0.1*pulse))
            if ob>3: place(frame,o3,W/2,800,ease_back((ob-3)/0.8))
        # confetti
        for c in conf:
            dt=t-c['t0']
            if 0<dt<1.6:
                x=c['x']+c['vx']*dt; y=c['y']+c['vy']*dt+900*dt*dt
                place(frame,STARS[c['k']],x,y,1.0,c['r']+c['vr']*dt,max(0,1-dt/1.6))
        ff.stdin.write(frame.tobytes())
    ff.stdin.close(); ff.wait()
    # audio
    SR=44100
    music.make(total+0.5,out=f'{S}/abed{ep}.wav',seed=(sum(map(ord,str(ep)))%97)+3)
    def load(p):
        raw=subprocess.check_output(['ffmpeg','-v','error','-i',p,'-f','s16le','-ac','1','-ar',str(SR),'-']); return np.frombuffer(raw,np.int16).astype(np.float32)/32768
    bed=load(f'{S}/abed{ep}.wav'); L_=int(total*SR); mix=np.zeros(L_+SR); v=np.zeros_like(mix)
    def put(p,beat):
        a=load(p); s=int(beat*BEAT*SR); n=min(len(a),len(v)-s); v[s:s+n]+=a[:n]
    put(f'{A}/intro{ep}.mp3',1.0)
    for i,L in enumerate(letters):
        base=INTRO+SEG*i
        for j,off in enumerate((0.15,4,8)): put(f'{A}/w{L}{j+1}.mp3',base+off)
    put(f'{A}/outro{ep}.mp3',INTRO+SEG*len(letters)+1)
    env=np.convolve(np.abs(v),np.ones(4410)/4410,'same'); duck=np.convolve(np.where(env>0.01,0.4,0.7),np.ones(8820)/8820,'same')
    n=min(len(bed),len(mix)); mix[:n]+=bed[:n]*duck[:n]; mix+=v*1.2; mix=mix[:L_]
    fo=int(0.8*SR); mix[-fo:]*=np.linspace(1,0,fo); mix/=max(1,np.abs(mix).max()/0.95)
    w=wave.open(f'{S}/amix{ep}.wav','wb'); w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((mix*32767).astype(np.int16).tobytes()); w.close()
    subprocess.run(['ffmpeg','-y','-v','error','-i',f'{S}/anim_v{ep}.mp4','-i',f'{S}/amix{ep}.wav','-c:v','copy','-af','loudnorm=I=-14:TP=-1.5:LRA=11','-c:a','aac','-b:a','192k','-shortest','-movflags','+faststart',outname],check=True)
    print('done',outname,round(total,2),os.path.getsize(outname))
if __name__=='__main__':
    import json
    Wd=json.load(open('/home/claude/ss/words.json')); Wd.update({'I':['Ice cream'],'J':['Juice'],'K':['Kite'],'L':['Lion']})
    EPS={'4':('ABCD','IJKL'),'5':('EFGH','JKLI'),'6':('MNOP','MNOP'),'7':('QRST','QRST'),'8':('UVWX','UVWX'),'9':('YZ','YZKI'),'AZ':('ABCDEFGHIJKLMNOPQRSTUVWXYZ','IJKL')}
    for ep in sys.argv[1:]:
        ls,party=EPS[ep]
        build(ep,list(ls),[Wd[L][0] for L in ls],None,("Let's sing",),'Yay! You know' if ep!='AZ' else 'You know A to Z!',f'/home/claude/ss/ss_ep{ep}.mp4',party_letters=party)
