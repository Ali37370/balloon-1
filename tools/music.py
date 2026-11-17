import numpy as np, wave, sys
SR=44100
def ks(freq,dur,decay=0.996,bright=0.5):
    n=int(SR*dur); N=int(SR/freq)
    buf=np.random.uniform(-1,1,N)*bright
    out=np.zeros(n)
    for i in range(n):
        out[i]=buf[i%N]
        buf[i%N]=decay*0.5*(buf[i%N]+buf[(i+1)%N])
    return out
def note(m): return 440*2**((m-69)/12)
def env(n,a=0.005,r=0.1):
    e=np.ones(n);A=int(a*SR);R=int(r*SR)
    e[:A]=np.linspace(0,1,A);e[-R:]*=np.linspace(1,0,R);return e
def make(seconds,bpm=116,out='bed.wav',seed=1):
    np.random.seed(seed)
    beat=60/bpm; total=int(SR*seconds)+SR
    mix=np.zeros(total)
    chords=[[60,64,67],[55,59,62],[57,60,64],[53,57,60]]  # C G Am F
    bass=[36,43,45,41]
    mel=[72,74,76,79, 79,76,74,72, 76,77,79,81, 79,77,76,74]
    t=0.0; bar=0; cache={}
    def pk(m,d,dec,br):
        k=(m,d,dec,br)
        if k not in cache: cache[k]=ks(note(m),d,dec,br)
        return cache[k]
    while t<seconds:
        c=chords[bar%4]
        for b in range(4):  # strum each beat, eighth pattern
            for s in (0,0.5):
                st=int((t+(b+s)*beat)*SR)
                for j,m in enumerate(c):
                    x=pk(m+12,0.6,0.995,0.35)
                    o=st+j*180
                    if o+len(x)<total: mix[o:o+len(x)]+=x*(0.22 if s==0 else 0.14)
            # bass on beats 1,3
            if b in (0,2):
                st=int((t+b*beat)*SR); f=note(bass[bar%4]); d=int(beat*SR*0.9)
                tt=np.arange(d)/SR; x=np.sin(2*np.pi*f*tt)*np.exp(-tt*3)*0.35
                if st+d<total: mix[st:st+d]+=x
            # kick + shaker
            st=int((t+b*beat)*SR); d=int(0.15*SR); tt=np.arange(d)/SR
            k=np.sin(2*np.pi*(120*np.exp(-tt*25)+45)*tt)*np.exp(-tt*18)*(0.5 if b in(0,2) else 0.0)
            if st+d<total: mix[st:st+d]+=k
            for s in (0.5,):
                st2=int((t+(b+s)*beat)*SR); d2=int(0.06*SR)
                sh=np.random.randn(d2)*np.exp(-np.arange(d2)/SR*60)*0.06
                if st2+d2<total: mix[st2:st2+d2]+=np.diff(np.concatenate([[0],sh]))
            # clap on 2,4
            if b in (1,3):
                d2=int(0.1*SR); cl=np.random.randn(d2)*np.exp(-np.arange(d2)/SR*30)*0.12
                if st+d2<total: mix[st:st+d2]+=cl
        # glockenspiel melody, light
        for i in range(4):
            m=mel[(bar*4+i)%16]; st=int((t+i*beat)*SR); d=int(0.5*SR); tt=np.arange(d)/SR
            x=(np.sin(2*np.pi*note(m+12)*tt)+0.3*np.sin(2*np.pi*note(m+24)*tt))*np.exp(-tt*6)*0.07
            if st+d<total: mix[st:st+d]+=x
        t+=4*beat; bar+=1
    mix=mix[:int(SR*seconds)]
    fo=int(1.5*SR); mix[-fo:]*=np.linspace(1,0,fo)
    mix/=np.max(np.abs(mix))+1e-9; mix*=0.8
    st=np.stack([mix,mix],1)
    w=wave.open(out,'wb');w.setnchannels(2);w.setsampwidth(2);w.setframerate(SR)
    w.writeframes((st*32767).astype(np.int16).tobytes());w.close()
if __name__=='__main__':
    make(float(sys.argv[1]),out=sys.argv[2])
