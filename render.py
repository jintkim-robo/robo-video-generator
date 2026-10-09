# Robo Video Generator renderer — design tokens: Robo-Design-System (robo-coop, dark)
import json,math,subprocess,io,re,sys
import numpy as np, cairosvg, os
CFG=json.load(open(os.environ.get('RVG_CONFIG','config.json')))
base=os.path.dirname(os.path.abspath(os.environ.get('RVG_CONFIG','config.json')))
P=lambda p:os.path.join(base,os.path.expanduser(p))
from PIL import Image,ImageDraw,ImageFont,ImageFilter
W,H,FPS=720,1280,30
DS=P(CFG['logo_dir'])+'/'
C=dict(bg=(15,23,42),black=(13,15,18),white=(245,245,240),blue=(30,64,175),cyan=(6,182,212),amber=(245,158,11),steel=(71,85,105),green=(16,185,129))
R=dict(md=8,lg=16,xl=24,pill=999)
JP=P(CFG['font_jp_bold']); JPR=P(CFG['font_jp_regular'])
RB=P(CFG['font_latin'])
_fc={}
def F(sz,kind='jp'):
    k=(sz,kind)
    if k not in _fc:
        if kind=='jp': f=ImageFont.truetype(JP,sz,index=0)
        elif kind=='jpr': f=ImageFont.truetype(JPR,sz,index=0)
        else:
            f=ImageFont.truetype(RB,sz)
            f.set_variation_by_name('Bold' if kind=='rb' else 'Regular')
        _fc[k]=f
    return _fc[k]
def svg(name,w):
    if not os.path.exists(DS+name):  # logo not available: text placeholder
        im=Image.new('RGBA',(w,w//2 if 'vertical' in name else w),(0,0,0,0)); dd=ImageDraw.Draw(im)
        dd.text((10,10),'LOGO',font=ImageFont.truetype(RB,w//5),fill=(245,245,240,255)); return im
    return Image.open(io.BytesIO(cairosvg.svg2png(url=DS+name,output_width=w))).convert('RGBA')
MARK=svg(CFG['logo_mark'],300); VERT=svg(CFG['logo_vertical'],380)
def ease(t):  # approx cubic-bezier(0.16,1,0.3,1)
    t=min(max(t,0),1); return 1-(1-t)**4
def lerp(a,b,t): return a+(b-a)*t
S=json.load(open('script.json')); T=json.load(open('durs.json'))
LG,SP=0.12,0.30  # gap between lines, pad at scene end
SUB=[];AUD=[];dur=[];t=0.0
for i,sc in enumerate(S):
    t0=t
    for j,l in enumerate(sc['lines']):
        SUB.append((t,t+T[i][j],l['sub'].rstrip('、。'))); AUD.append((t,f'a{i}_{j}.wav')); t+=T[i][j]+LG
    t+=SP-LG; dur.append(t-t0)
starts=np.cumsum([0]+dur[:-1]); TOTAL=sum(dur)
XF=0.35
# background: deep-circuit + drifting cyan/blue/amber glows + grid
yy,xx=np.mgrid[0:H,0:W].astype(np.float32)
def background(t):
    img=np.zeros((H,W,3),np.float32); img[:]=C['bg']
    for col,cx,cy,r,ph in [(C['blue'],0.2,0.25,520,0),(C['cyan'],0.85,0.7,420,2),(C['amber'],0.3,0.95,300,4)]:
        x=W*(cx+0.08*math.sin(t*0.5+ph)); y=H*(cy+0.05*math.cos(t*0.4+ph))
        g=np.exp(-((xx-x)**2+(yy-y)**2)/(2*r*r))[...,None]*0.45
        img=img*(1-g)+np.array(col,np.float32)*g
    return img
GRID=Image.new('RGBA',(W,H+48),(0,0,0,0)); gd=ImageDraw.Draw(GRID)
for x in range(0,W,48): gd.line([(x,0),(x,H+48)],fill=(245,245,240,14))
for y in range(0,H+48,48): gd.line([(0,y),(W,y)],fill=(245,245,240,14))
def rr(d,box,r,fill=None,outline=None,w=2): d.rounded_rectangle(box,radius=r,fill=fill,outline=outline,width=w)
def ctext(d,y,s,f,fill,x=W//2):
    b=d.textbbox((0,0),s,font=f); d.text((x-(b[2]-b[0])//2-b[0],y),s,font=f,fill=fill)
def a(c,al): return tuple(c)+(int(255*max(0,min(1,al))),)
def label(d,y,s,col=C['cyan']):
    f=F(28,'rb'); b=d.textbbox((0,0),s,font=f); w=b[2]+48
    rr(d,(W//2-w//2,y-4,W//2+w//2,y+48),R['pill'],fill=a(col,0.16),outline=a(col,0.9)); ctext(d,y+3,s,f,col)
# ---------- scenes: each draws on RGBA layer, lt = local time ----------
def sc_hook(L,lt,d):
    label(d,170,'EVERY DAY')
    ctext(d,240,'毎日の、',F(64),C['white']); ctext(d,320,'同じ作業。',F(64),C['amber'])
    items=[('メールの返信','12件'),('請求書の作成','3件'),('日程の調整','5件'),('議事録の整理','2件'),('報告書の更新','4件')]
    for i,(s,n) in enumerate(items):
        p=ease((lt-0.3-i*0.45)/0.6); 
        if p<=0: continue
        y=470+i*112+(1-p)*60; x0=110+int(6*math.sin(i)); al=p
        rr(d,(x0,y,W-110,y+92),R['xl'],fill=a((255,255,255),0.07*al+0.02),outline=a(C['white'],0.18*al))
        d.ellipse((x0+28,y+30,x0+60,y+62),outline=a(C['amber'],al),width=4)
        d.text((x0+82,y+24),s,font=F(32),fill=a(C['white'],al))
        f=F(26); b=d.textbbox((0,0),n,font=f)
        rr(d,(W-140-b[2]-24,y+26,W-140,y+66),R['pill'],fill=a(C['amber'],0.2*al)); d.text((W-152-b[2],y+30),n,font=f,fill=a(C['amber'],al))
def sc_logo(L,lt,d):
    p=ease(lt/0.9); s=int(300*lerp(0.7,1,p))
    m=MARK.resize((s,s)); m.putalpha(m.getchannel('A').point(lambda v:int(v*p)))
    # cyan ring pulse
    rad=200+40*math.sin(lt*2); d.ellipse((W//2-rad,440-rad,W//2+rad,440+rad),outline=a(C['cyan'],0.35*p),width=3)
    L.alpha_composite(m,(W//2-s//2,440-s//2))
    q=ease((lt-0.5)/0.8)
    ctext(d,690+int((1-q)*30),'Robo Co-op',F(76,'rb'),a(C['white'],q))
    ctext(d,790+int((1-q)*30),'Human−Machine Cooperative OS',F(30,'rb'),a(C['cyan'],q))
    q2=ease((lt-1.1)/0.8); ctext(d,860,'人とAIが、一緒に働く。',F(40),a(C['white'],q2))
def sc_tasks(L,lt,d):
    label(d,170,'AUTOMATE'); ctext(d,240,'まかせられる仕事',F(56),C['white'])
    cards=[('メールの整理','Inbox',C['cyan']),('資料づくり','Docs',C['amber']),('スケジュール調整','Calendar',C['green'])]
    for i,(s,e,col) in enumerate(cards):
        p=ease((lt-0.2-i*0.9)/0.7)
        if p<=0: continue
        y=380+i*230; x=int(lerp(W,80,p))
        rr(d,(x,y,x+W-160,y+190),R['xl'],fill=a((255,255,255),0.08),outline=a(col,0.8))
        rr(d,(x+30,y+30,x+110,y+110),R['lg'],fill=a(col,0.9))
        d.text((x+130,y+28),e,font=F(28,'rb'),fill=a(col,1)); d.text((x+130,y+66),s,font=F(40),fill=C['white'])
        done=ease((lt-1.0-i*0.9)/0.5)
        rr(d,(x+30,y+140,x+30+int((W-220)*done),y+152),R['pill'],fill=a(col,0.9))
def sc_fleet(L,lt,d):
    label(d,170,'AGENT FLEET',C['green']); ctext(d,240,'くり返しは、エージェントへ',F(46),C['white'])
    cx,cy=W//2,700; nodes=6; p=ease(lt/1.0)
    pts=[(cx+int(230*p*math.cos(k*2*math.pi/nodes-math.pi/2)),cy+int(230*p*math.sin(k*2*math.pi/nodes-math.pi/2))) for k in range(nodes)]
    names=['Mail','Docs','Cal','Research','Ops','Notes']
    for k,(x,y) in enumerate(pts):
        d.line([(cx,cy),(x,y)],fill=a(C['cyan'],0.4),width=3)
        f=(lt*0.7+k/nodes)%1; px,py=lerp(x,cx,f),lerp(y,cy,f); d.ellipse((px-7,py-7,px+7,py+7),fill=a(C['amber'],p))
    for k,(x,y) in enumerate(pts):
        rr(d,(x-62,y-40,x+62,y+40),R['lg'],fill=a(C['black'],0.9),outline=a(C['cyan'],p))
        ctext(d,y-16,names[k],F(28,'rb'),a(C['cyan'],p),x)
    rr(d,(cx-90,cy-90,cx+90,cy+90),R['pill'],fill=C['white']); ctext(d,cy-26,'あなた',F(36),C['black'],cx)
    q=ease((lt-1.5)/0.8); ctext(d,1010,'人は、大事な仕事に集中。',F(42),a(C['amber'],q))
def sc_comm(L,lt,d):
    label(d,170,'COMMUNITY',C['amber']); ctext(d,240,'メンバー同士で',F(56),C['white']); ctext(d,316,'学び合う',F(56),C['cyan'])
    pos=[(200,520),(520,500),(360,660),(160,820),(560,820),(360,960)]; cols=[C['cyan'],C['amber'],C['green'],C['blue'],C['cyan'],C['amber']]
    for i in range(len(pos)):
        for j in range(i+1,len(pos)):
            if (i+j)%2: 
                q=ease((lt-0.4)/1.0); x1,y1=pos[i];x2,y2=pos[j]
                d.line([(x1,y1),(lerp(x1,x2,q),lerp(y1,y2,q))],fill=a(C['white'],0.22),width=2)
    for i,(x,y) in enumerate(pos):
        p=ease((lt-i*0.15)/0.6); r=int(54*p)+int(3*math.sin(lt*3+i))
        if r>0: d.ellipse((x-r,y-r,x+r,y+r),fill=a(cols[i],0.9),outline=a(C['white'],0.8),width=3)
    for i,(s,x,y) in enumerate([('ツール選び',200,420),('導入',520,400),('運用のコツ',360,1060)]):
        q=ease((lt-1.0-i*0.4)/0.6); f=F(26); b=d.textbbox((0,0),s,font=f); w=b[2]+36
        rr(d,(x-w//2,y-22,x+w//2,y+26),R['pill'],fill=a(C['black'],0.85*q),outline=a(C['white'],0.4*q)); ctext(d,y-18,s,f,a(C['white'],q),x)
def sc_pillars(L,lt,d):
    label(d,170,'ROBO CO-OP'); 
    rows=[('Learn','学ぶ',C['cyan']),('Build','つくる',C['amber']),('Share','分かち合う',C['green'])]
    for i,(e,j,col) in enumerate(rows):
        p=ease((lt-i*0.6)/0.7); y=330+i*230+int((1-p)*40)
        rr(d,(90,y,W-90,y+190),R['xl'],fill=a(col,0.14*p),outline=a(col,p))
        d.text((130,y+28),e,font=F(34,'rb'),fill=a(col,p)); d.text((130,y+80),j,font=F(64),fill=a(C['white'],p))
def sc_end(L,lt,d):
    p=ease(lt/0.9); v=VERT.copy(); v.putalpha(v.getchannel('A').point(lambda x:int(x*p)))
    L.alpha_composite(v,(W//2-v.width//2,260+int((1-p)*30)))
    q=ease((lt-0.6)/0.8); y=260+v.height+70
    ctext(d,y,'あなたのチームの',F(44),a(C['white'],q)); ctext(d,y+64,'「めんどう」を教えてください',F(44),a(C['amber'],q))
    q2=ease((lt-1.2)/0.7); f=F(30); s='Updating Humanity through Solidarity.'; f2=F(26,'rb')
    rr(d,(140,y+170,W-140,y+250),R['pill'],fill=a(C['cyan'],q2)); ctext(d,y+188,'まずは、ひとつから',f,a(C['black'],q2))
    ctext(d,y+290,s,f2,a(C['white'],0.7*q2))
SHOT={}
def sc_shot(L,lt,d,sc,dd):
    if sc['img'] not in SHOT:
        fp=P(os.path.join(CFG['shots_dir'],sc['img']))
        if os.path.exists(fp): im=Image.open(fp).convert('RGB')
        else:  # placeholder when screenshot missing
            im=Image.new('RGB',(1440,1000),(30,41,59)); ImageDraw.Draw(im).text((80,440),'screenshot: '+sc['img'],font=F(60),fill=(148,163,184))
        fw=1000; SHOT[sc['img']]=im.resize((fw,int(im.height*fw/im.width)),Image.LANCZOS)
    im=SHOT[sc['img']]
    label(d,150,sc['tag'],C['cyan']); ctext(d,220,sc['title'],F(50),C['white'])
    p=ease(lt/0.8); fx0,fy0,fx1,fy1=50,330+int((1-p)*60),W-50,1080+int((1-p)*60)
    # device/card mockup: raised surface, xl radius, window bar
    sh=Image.new('RGBA',(W,H),(0,0,0,0)); ImageDraw.Draw(sh).rounded_rectangle((fx0+6,fy0+18,fx1+6,fy1+18),R['xl'],fill=(0,0,0,int(120*p))); L.alpha_composite(sh.filter(ImageFilter.GaussianBlur(14)))
    rr(d,(fx0,fy0,fx1,fy1),R['xl'],fill=a(C['black'],p),outline=a(C['cyan'],0.7*p),w=3)
    for k,cc in enumerate([C['amber'],C['green'],C['cyan']]): d.ellipse((fx0+24+k*28,fy0+20,fx0+40+k*28,fy0+36),fill=a(cc,p))
    vx0,vy0,vx1,vy1=fx0+14,fy0+52,fx1-14,fy1-14; vw,vh=vx1-vx0,vy1-vy0
    k=min(lt/dd,1); z=lerp(1.0,1.18,k); cw,ch=int(vw/z*im.width/ max(vw,1)*vw/im.width*1.0),0
    sw=int(im.width/z); shh=int(sw*vh/vw)   # crop size in img px (img scaled 1000 wide)
    sw=min(sw,im.width); shh=min(shh,im.height)
    cx=int((im.width-sw)/2); cy=int(lerp(0,im.height-shh,k))
    crop=im.crop((cx,cy,cx+sw,cy+shh)).resize((vw,vh),Image.BILINEAR).convert('RGBA')
    m=Image.new('L',(vw,vh),0); ImageDraw.Draw(m).rounded_rectangle((0,0,vw,vh),R['lg'],fill=int(255*p)); crop.putalpha(m)
    L.alpha_composite(crop,(vx0,vy0))
SC=dict(shot=sc_shot,hook=sc_hook,logo=sc_logo,tasks=sc_tasks,fleet=sc_fleet,community=sc_comm,pillars=sc_pillars,end=sc_end)
def scene_layer(i,t):
    lt=t-starts[i]; L=Image.new('RGBA',(W,H),(0,0,0,0)); d=ImageDraw.Draw(L)
    zoom=1+0.03*(lt/dur[i])  # subtle push-in
    sc=S[i]
    if sc['scene']=='shot': sc_shot(L,lt,d,sc,dur[i])
    else: SC[sc['scene']](L,lt,d)
    if zoom!=1:
        nw,nh=int(W*zoom),int(H*zoom); L=L.resize((nw,nh),Image.BILINEAR).crop(((nw-W)//2,(nh-H)//2,(nw-W)//2+W,(nh-H)//2+H))
    return L
def draw_sub(L,t):
    for a0,a1,s in SUB:
        if a0<=t<a1:
            d=ImageDraw.Draw(L); f=F(44); b=d.textbbox((0,0),s,font=f); w=b[2]-b[0]+56
            y=1130; f=F(44 if len(s)<=12 else 38); b=d.textbbox((0,0),s,font=f); w=b[2]-b[0]+56
            rr(d,(W//2-w//2,y,W//2+w//2,y+84),R['pill'],fill=(13,15,18,215),outline=a(C['cyan'],0.6))
            ctext(d,y+42-(b[3]+b[1])//2,s,f,C['white'])
srt=open('subtitles.srt','w')
def ts(x): return f"{int(x//3600):02}:{int(x%3600//60):02}:{int(x%60):02},{int(x*1000%1000):03}"
for k,(a0,a1,s) in enumerate(SUB): srt.write(f"{k+1}\n{ts(a0)} --> {ts(a1)}\n{s}\n\n")
srt.close()
N=int(TOTAL*FPS)
ff=subprocess.Popen(['ffmpeg','-y','-loglevel','error','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(FPS),'-i','-','-c:v','libx264','-preset','medium','-crf','20','-pix_fmt','yuv420p','video.mp4'],stdin=subprocess.PIPE)
for n in range(N):
    t=n/FPS
    bg=Image.fromarray(background(t).clip(0,255).astype(np.uint8)).convert('RGBA')
    off=int(t*12)%48; bg.alpha_composite(GRID.crop((0,off,W,off+H)))
    i=int(np.searchsorted(starts,t,side='right')-1)
    lay=scene_layer(i,t)
    # crossfade over the next scene's start (no dark flash: blend layers over shared bg)
    if i+1<len(S) and t>starts[i+1]-XF:
        k=(t-(starts[i+1]-XF))/XF; nxt=scene_layer(i+1,starts[i+1]+0.0)
        lay=Image.blend(lay,nxt,0)  # keep
        lay.putalpha(lay.getchannel('A').point(lambda v:int(v*(1-k))))
        bg.alpha_composite(lay); lay=None
    if i>0 and t-starts[i]<XF:
        k=(t-starts[i])/XF; lay.putalpha(lay.getchannel('A').point(lambda v:int(v*k)))
    if lay is not None: bg.alpha_composite(lay)
    draw_sub(bg,t)
    ff.stdin.write(bg.convert('RGB').tobytes())
    if n%150==0: print(n,N,flush=True)
ff.stdin.close(); ff.wait()

inp=[];fc=''
for k,(t0,f) in enumerate(AUD): inp+=['-i',f]; fc+=f'[{k}:a]adelay={int(t0*1000)}:all=1[d{k}];'
fc+=''.join(f'[d{k}]' for k in range(len(AUD)))+f'amix=inputs={len(AUD)}:normalize=0,apad=whole_dur={TOTAL}[a]'
subprocess.run(['ffmpeg','-y','-loglevel','error',*inp,'-filter_complex',fc,'-map','[a]','-ar','44100','-c:a','aac','-b:a','128k','audio.m4a'],check=True)
print('total',TOTAL)
