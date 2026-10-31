# -*- coding: utf-8 -*-
"""Earth-stops short video: original animated scenes + genuine Edge YunzeNeural TTS."""
import os, math, wave, asyncio, subprocess, json
from pathlib import Path
import numpy as np
import cv2
from PIL import Image,ImageDraw,ImageFont
from opencc import OpenCC

ROOT=Path(__file__).resolve().parent
OUT=ROOT/"output"; OUT.mkdir(exist_ok=True)
SENTENCES=[
"如果有一天，地球突然停止转动，会发生什么？",
"先别急着说，终于不用早起了。",
"真正可怕的事情，从第一秒就开始了。",
"我们站在地面上，看起来一动不动。",
"但实际上，地球正带着我们一起飞速旋转。",
"如果地球突然停下，你、汽车、海水，甚至空气，都不会立刻停下来。",
"它们会因为惯性，继续向前冲。",
"强风横扫城市，海水涌向陆地，",
"建筑物和道路都会遭到严重破坏。",
"而这，还只是开始。",
"如果地球停止自转，但仍然绕着太阳公转，",
"一个地方的白天和黑夜，就会变得漫长得多。",
"太阳可能连续几个月挂在天上，地面持续升温；",
"接着又是漫长的黑夜，气温不断下降。",
"农作物难以生长，",
"原本熟悉的四季和生活节奏，也会彻底改变。",
"好消息是，地球不会毫无征兆地突然停转。",
"这样的画面，只是一个极端假设。",
"但想想也挺有意思：",
"我们每天抱怨时间过得太快，",
"却很少注意到，脚下这颗星球，一直在不停转动。",
"如果地球真的停下来，而你还有一分钟可以做选择，",
"你最想做什么？"]
SCENES=[0,0,1,1,1,2,2,3,3,3,4,4,5,6,7,7,8,8,8,8,8,9,9]
TITLES=["地球突然停轉","慣性的第一秒","萬物繼續前進","狂風與海嘯","晝夜不再交替","漫長的烈日","漫長的黑夜","農業與生態危機","極端假設","你會做什麼？"]
VOICE="zh-CN-YunzeNeural"
W,H,FPS=450,800,15
cc=OpenCC("s2t")
def cmd(args):
    subprocess.run(args,check=True)
async def tts():
    import edge_tts
    for i,s in enumerate(SENTENCES):
        f=OUT/f"voice_{i:02}.mp3"
        if f.exists() and f.stat().st_size>1000:continue
        for n in range(3):
            try:
                await edge_tts.Communicate(s,VOICE,rate="-4%",pitch="-2Hz").save(str(f))
                if f.stat().st_size<1000:raise RuntimeError("TTS returned empty audio")
                break
            except Exception:
                if n==2:raise
                await asyncio.sleep(3+5*n)
def audio():
    sr=24000;blocks=[np.zeros(int(.5*sr),dtype=np.float32)];cues=[];now=.5
    for i,s in enumerate(SENTENCES):
        wav=OUT/f"voice_{i:02}.wav"
        cmd(["ffmpeg","-y","-loglevel","error","-i",str(OUT/f"voice_{i:02}.mp3"),"-ar",str(sr),"-ac","1",str(wav)])
        with wave.open(str(wav),"rb") as f:
            arr=np.frombuffer(f.readframes(f.getnframes()),dtype="<i2").astype(np.float32)/32768
        end=now+len(arr)/sr
        cues.append(dict(start=now,end=end,scene=SCENES[i],text=cc.convert(s)))
        blocks.append(arr);pause=.27 if i in (1,4,9,11,13,15,20) else .14
        blocks.append(np.zeros(round(sr*pause),np.float32));now=end+pause
    blocks.append(np.zeros(sr,np.float32))
    pcm=np.concatenate(blocks);t=np.arange(len(pcm),dtype=np.float32)/sr
    # self-generated quiet bass drone; no external copyrighted music
    bass=(.007*np.sin(t*2*np.pi*55)+.005*np.sin(t*2*np.pi*82.4))
    env=np.minimum(1,t/1.5)*np.minimum(1,(len(pcm)/sr-t)/1.5)
    pcm=np.clip(pcm*.95+bass*env,-.98,.98)
    with wave.open(str(OUT/"audio.wav"),"wb") as f:
        f.setnchannels(1);f.setsampwidth(2);f.setframerate(sr)
        f.writeframes(np.int16(pcm*32767).tobytes())
    def stamp(x):
        n=round(x*1000);h,n=divmod(n,3600000);m,n=divmod(n,60000);s,n=divmod(n,1000)
        return f"{h:02}:{m:02}:{s:02},{n:03}"
    def wrap(s,width=13):
        for punctuation in ["，","；","："]:s=s.replace(punctuation,punctuation+"\n")
        lines=[]
        for piece in s.splitlines():
            lines.extend(piece[j:j+width] for j in range(0,len(piece),width))
        return "\n".join(lines[:4])
    for c in cues:c["caption"]=wrap(c["text"])
    (OUT/"earth_stops_tc.srt").write_text("".join(f'{i+1}\n{stamp(c["start"])} --> {stamp(c["end"])}\n{c["caption"]}\n\n' for i,c in enumerate(cues)),encoding="utf-8")
    (OUT/"timeline.json").write_text(json.dumps(dict(voice=VOICE,cues=cues),ensure_ascii=False,indent=2),encoding="utf-8")
    return cues,len(pcm)/sr
random=np.random.default_rng(1228)
STARS=[(int(random.integers(W)),int(random.integers(H)),int(random.integers(1,3)),float(random.uniform(0,6))) for _ in range(140)]
TEX=np.zeros((230,460,3),np.uint8);TEX[:]=(110,67,22)
for _ in range(85):
    cv2.ellipse(TEX,(int(random.integers(460)),int(random.integers(230))),(int(random.integers(6,30)),int(random.integers(3,20))),int(random.integers(180)),0,360,(48,110,70),-1)
for _ in range(125):
    cv2.ellipse(TEX,(int(random.integers(460)),int(random.integers(230))),(int(random.integers(8,30)),2),int(random.integers(180)),0,360,(180,211,222),1)
SPHERES={}
def globe(f,x,y,r,t):
    if r not in SPHERES:
        yy,xx=np.mgrid[-r:r+1,-r:r+1].astype(np.float32)
        q=(xx*xx+yy*yy)/r**2
        z=np.sqrt(np.clip(1-q,0,1))
        lon=np.arctan2(xx/r,z);lat=np.arcsin(np.clip(-yy/r,-1,1))
        sh=np.clip(.23+.78*(.55*z-.55*xx/r-.15*yy/r),.16,1)
        SPHERES[r]=(q<=1,lon,lat,sh)
    mask,lon,lat,sh=SPHERES[r]
    mx=(((lon+t*.10+1.2)%(2*np.pi))/(2*np.pi)*459).astype(np.float32)
    my=((np.pi/2-lat)/np.pi*229).astype(np.float32)
    disk=cv2.remap(TEX,mx,my,cv2.INTER_LINEAR,borderMode=cv2.BORDER_WRAP)
    disk=np.uint8(np.clip(disk.astype(np.float32)*sh[:,:,None],0,255))
    l=max(0,x-r);rr=min(W,x+r+1);a=max(0,y-r);b=min(H,y+r+1)
    if l>=rr or a>=b:return
    piece=disk[a-y+r:b-y+r,l-x+r:rr-x+r]
    valid=mask[a-y+r:b-y+r,l-x+r:rr-x+r]
    f[a:b,l:rr][valid]=piece[valid]
    cv2.circle(f,(x,y),r+3,(145,106,48),2,cv2.LINE_AA)
def city(f,t,wave=False,ice=False,hot=False):
    f[:]=(60,86,125) if hot else ((46,39,37) if ice else (46,31,19))
    cv2.circle(f,(348 if hot else 72,175),78,(82,156,248) if hot else (68,84,101),-1)
    rr=np.random.default_rng(64);x=0
    while x<W:
        ww=int(rr.integers(20,40));hh=int(rr.integers(110,300));yy=H-165-hh
        cv2.rectangle(f,(x,yy),(x+ww,H-165),(37,34,30),-1)
        for xx in range(x+6,x+ww-3,10):
            for y in range(yy+12,H-174,15):
                if (xx+y)%4:cv2.rectangle(f,(xx,y),(xx+3,y+5),(88,101,118),-1)
        x+=ww+4
    cv2.rectangle(f,(0,H-165),(W,H),(38,41,48) if not ice else (114,120,129),-1)
    if wave:
        base=H-125-int(160*(.5+.5*math.sin(t*.33)))
        overlay=f.copy()
        poly=np.array([[0,base],[W,base-10],[W,H],[0,H]],np.int32)
        cv2.fillPoly(overlay,[poly],(131,79,43))
        cv2.addWeighted(overlay,.85,f,.15,0,f)
        for i in range(5):
            yy=base+i*27
            pts=np.array([[xx,int(yy+12*math.sin(xx*.03+t*1.6+i))] for xx in range(0,W+1,6)],np.int32)
            cv2.polylines(f,[pts],False,(177,133,84),3,cv2.LINE_AA)
    if ice:
        for i in range(105):
            x=int((i*97+t*22)%W);y=int((i*73+t*43)%H)
            cv2.circle(f,(x,y),1,(228,226,214),-1)
    elif not hot:
        for i in range(85):
            x=int((i*79+t*235)%(W+110))-55;y=int((i*61+t*91)%H)
            cv2.line(f,(x,y),(x+35,y-9),(105,132,153),1,cv2.LINE_AA)
def scene_image(scene,t):
    f=np.zeros((H,W,3),np.uint8);f[:]=(24,16,9)
    for x,y,r,p in STARS:
        v=int(110+110*(.5+.5*math.sin(t*.5+p)))
        cv2.circle(f,(x,y),r,(v,v,v),-1)
    if scene in (0,1,4,8,9):
        radius=160 if scene!=9 else 134
        globe(f,W//2,350,radius,t)
        if scene==1:cv2.arrowedLine(f,(40,565),(W-40,565),(91,215,244),4,cv2.LINE_AA)
        if scene==4:
            cv2.circle(f,(72,167),44,(55,171,252),-1)
            cv2.circle(f,(377,167),26,(216,211,204),-1)
        if scene in (8,9):
            for i in range(3):
                cv2.ellipse(f,(W//2,350),(radius+i*11,int(radius*.4)+i*9),-15,180+t*6,320+t*6,(105,124,162),1)
    elif scene in (2,3,5,6):city(f,t,wave=scene==3,ice=scene==6,hot=scene==5)
    else:
        f[:]=(39,58,62);cv2.rectangle(f,(0,490),(W,H),(48,80,92),-1)
        for i in range(13):
            x=20+i*35
            cv2.line(f,(x,H-40),(x-15,525),(34,77,96),3)
            for j in range(3):cv2.ellipse(f,(x-20,540+j*60),(18,5),40,0,360,(35,106,115),-1)
    return f
def face(size,bold=True):
    paths=["/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc" if bold else "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Bold.ttc"]
    for p in paths:
        if os.path.exists(p):return ImageFont.truetype(p,size,index=2)
    return ImageFont.load_default()
F1=face(34);F2=face(28);F3=face(18,False)
def add_titles(f,scene,subtitle,t,total):
    im=Image.fromarray(cv2.cvtColor(f,cv2.COLOR_BGR2RGB)).convert("RGBA")
    layer=Image.new("RGBA",im.size,(0,0,0,0));d=ImageDraw.Draw(layer)
    d.rounded_rectangle((17,60,W-17,160),radius=12,fill=(5,15,27,220),outline=(70,179,201,140),width=2)
    d.text((31,71),f"EARTH SCIENCE   /   0{scene+1}",font=F3,fill=(137,212,232))
    d.text((31,105),TITLES[scene],font=F1,fill="white")
    if subtitle:
        lines=subtitle.splitlines()
        bh=27+len(lines)*42;top=H-215-bh
        d.rounded_rectangle((14,top,W-14,top+bh),radius=12,fill=(2,10,18,221))
        for i,line in enumerate(lines):
            width=d.textbbox((0,0),line,font=F2)[2]
            d.text(((W-width)/2,top+9+i*42),line,font=F2,fill="white")
    d.rectangle((0,H-18,int(W*min(1,t/total)),H-13),fill=(93,218,230))
    d.text((20,H-40),"極端假設 · 科學想像",font=F3,fill=(185,199,211))
    return cv2.cvtColor(np.asarray(Image.alpha_composite(im,layer).convert("RGB")),cv2.COLOR_RGB2BGR)
def render(cues,total):
    dst=OUT/"earth_stops_yunze.mp4"
    args=["ffmpeg","-y","-hide_banner","-loglevel","error","-f","rawvideo","-pix_fmt","bgr24","-s",f"{W}x{H}","-r",str(FPS),"-i","-","-i",str(OUT/"audio.wav"),"-vf","scale=720:1280:flags=lanczos","-c:v","libx264","-preset","veryfast","-crf","22","-pix_fmt","yuv420p","-c:a","aac","-b:a","160k","-movflags","+faststart","-t",str(total),str(dst)]
    p=subprocess.Popen(args,stdin=subprocess.PIPE)
    index=0
    try:
        for i in range(math.ceil(total*FPS)):
            t=i/FPS
            while index<len(cues)-1 and t>cues[index]["end"]:index+=1
            c=cues[index]
            subtitle=c["caption"] if c["start"]<=t<=c["end"] else ""
            f=scene_image(c["scene"],t)
            p.stdin.write(add_titles(f,c["scene"],subtitle,t,total).tobytes())
    finally:p.stdin.close()
    if p.wait()!=0:raise RuntimeError("video encoding failed")
    print("CREATED",dst,round(total,2),"seconds",dst.stat().st_size,"bytes")
if __name__=="__main__":
    asyncio.run(tts())
    cues,total=audio()
    render(cues,total)
