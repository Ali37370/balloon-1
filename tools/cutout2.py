import sys
import numpy as np, cv2
from PIL import Image, ImageFilter
from scipy import ndimage
def cut(src,dst):
    img=cv2.imread(src); h,w=img.shape[:2]
    im=img.astype(np.int32)
    border=np.concatenate([im[0],im[-1],im[:,0],im[:,-1]]); bg=np.median(border,0)
    diff=np.sqrt(((im-bg)**2).sum(2))
    hsv=cv2.cvtColor(img,cv2.COLOR_BGR2HSV); sat=hsv[...,1]; val=hsv[...,2].astype(int); bv=int(bg.max())
    mask=np.full((h,w),cv2.GC_PR_BGD,np.uint8)
    # border strip definite bg
    mask[:8,:]=0; mask[-8:,:]=0; mask[:,:8]=0; mask[:,-8:]=0
    bgl=(diff<10); lab,_=ndimage.label(bgl)
    edge=set(np.unique(np.concatenate([lab[0],lab[-1],lab[:,0],lab[:,-1]])))-{0}
    mask[np.isin(lab,list(edge))]=cv2.GC_BGD
    fg=(diff>55)|(sat>70)|(val>bv+25)
    fg=ndimage.binary_erosion(fg,iterations=2)
    mask[fg]=cv2.GC_PR_FGD
    core=ndimage.binary_erosion(fg,iterations=12); mask[core]=cv2.GC_FGD
    bgm=np.zeros((1,65),np.float64); fgm=np.zeros((1,65),np.float64)
    cv2.grabCut(img,mask,None,bgm,fgm,6,cv2.GC_INIT_WITH_MASK)
    m=((mask==1)|(mask==3))
    lab,n=ndimage.label(m)
    if n>1:
        sizes=ndimage.sum(m,lab,range(1,n+1)); keep=np.argmax(sizes)+1
        big=[i+1 for i,s in enumerate(sizes) if s>0.02*sizes.max()]
        m=np.isin(lab,big)
    m=ndimage.binary_fill_holes(m)
    if CLOSE: m=ndimage.binary_fill_holes(ndimage.binary_closing(m,iterations=CLOSE))
    rows=np.where(m.any(1))[0]; top,bot=rows[0],rows[-1]; H=bot-top
    band=m[int(top+0.55*H):int(top+0.82*H)]
    cols=np.where(band.any(0))[0]; x0,x1=cols[0]-12,cols[-1]+12
    low=int(top+0.82*H); m[low:,:max(0,x0)]=False; m[low:,x1:]=False
    a=Image.fromarray((m*255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.3))
    out=Image.open(src).convert('RGBA'); out.putalpha(a); out=out.crop(out.getbbox()); out.save(dst); print(dst,out.size)
CLOSE=int(sys.argv[2]) if len(sys.argv)>2 else 0
for c in sys.argv[1]: cut(f'/home/claude/balloon-1/assets/c{c}.png',f'/home/claude/ss/cut_{c}.png')
