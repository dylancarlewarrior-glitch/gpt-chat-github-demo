#!/usr/bin/env python3
# 老陈分享 · GitHub 开源软件短视频
# Real GitHub repository-page captures for editorial commentary; no mock software demos.
import os,re,io,math,json,sys,time,subprocess,requests
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont,ImageFilter
from pydub import AudioSegment
from opencc import OpenCC

P=Path("video_out");P.mkdir(exist_ok=True)
VOICE="zh-CN-YunzeNeural"; TC=OpenCC("s2twp")
# Each entry is an uninterrupted narration segment; captions are aligned to its generated audio.
SEGS=[
("開場","今天给你推荐五款 GitHub 上值得收藏的开源软件。不是那种装完就吃灰的玩具，而是真能省时间、帮你干活的工具。有的能让手机和电脑秒传文件，有的能把几十个 G 的视频剪得干干净净。最后一款，尤其适合办公族。","5 款開源實用神器","不靠噱頭，只看能不能解決問題",""),
("01","第一款，LocalSend。手机传文件到电脑，不想登录微信，不想开网盘，更不想忍受压缩画质？它让同一个局域网内的设备直接传文件。Windows、安卓、苹果设备都能用。无需账号，传大视频尤其顺手。注意，双方通常需要连接同一局域网。","LocalSend","手機電腦互傳｜無需帳號","localsend/localsend"),
("02","第二款，ShareX。Windows 用户的截图瑞士军刀。普通截图当然可以，但它还支持长截图、区域录屏、动图录制、图片标注，甚至 OCR 文字识别。尤其是经常做教程和工作汇报的人，熟悉快捷键以后，真的能省下不少时间。","ShareX","截圖、錄屏、OCR 一次搞定","ShareX/ShareX"),
("03","第三款，LosslessCut。剪视频最怕什么？不是剪错，而是导出等半天，还重新压缩画质。这个工具专攻快速裁切，在支持的格式和切点条件下，可以尽量直接复制原始音视频数据。处理行车记录仪、旅行素材和长视频粗剪，非常合适。","LosslessCut","快速裁切｜盡量避免重編碼","mifi/lossless-cut"),
("04","第四款，OBS Studio。想录游戏、录教学、做直播，先看它。窗口捕获、屏幕录制、多个画面切换，甚至直播推流，都能放在一个工作流里。它功能强，但新手第一次打开，可能会觉得设置很多。建议先学会场景、来源和声音混音这三样。","OBS Studio","螢幕錄製｜直播推流｜多場景","obsproject/obs-studio"),
("05","第五款，Stirling PDF。合并 PDF、拆分页面、压缩文件、做 OCR，不想一件事开五个网站，可以试试它。它有能自己部署的版本，也提供不同的服务和付费能力。这里提醒一句：项目现在采用开放核心模式，不要把所有功能都误认为完全免费开源。","Stirling PDF","PDF 合併、分割、壓縮、OCR","Stirling-Tools/Stirling-PDF"),
("結尾","怎么选？手机电脑传文件，先装 LocalSend。Windows 高频截图，选 ShareX。视频粗剪，试 LosslessCut。录屏直播，装 OBS。PDF 处理多，就研究 Stirling PDF。所有项目地址我都放在资料清单里。收藏这期，下一次介绍更狠的开源神器。","你的工具箱，該升級了","官方 GitHub 原始專案｜請辨識正版","")
]
FONT="/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
FONT2="/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
def font(sz,bold=False):
    for path in [FONT if bold else FONT2,"/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"]:
        if os.path.exists(path):return ImageFont.truetype(path,sz)
    return ImageFont.load_default()
def textwrap_px(s, f, maxw):
    lines=[];cur=""
    for ch in s:
        if ImageDraw.Draw(Image.new("RGB",(1,1))).textbbox((0,0),cur+ch,font=f)[2] > maxw and cur:
            lines.append(cur);cur=ch
        else:cur+=ch
    if cur:lines.append(cur)
    return lines
def rr(d, box, fill,r=24,outline=None,width=2):
    d.rounded_rectangle(box,radius=r,fill=fill,outline=outline,width=width)
def render_card(i,row,shot=None):
    sec,script,name,desc,repo=row
    W,H=720,1280
    im=Image.new("RGB",(W,H),(10,16,28));d=ImageDraw.Draw(im)
    # Subtle grid and two luminous disks
    for x in range(0,W,72):d.line((x,0,x,H),fill=(19,31,46),width=1)
    for y in range(0,H,72):d.line((0,y,W,y),fill=(19,31,46),width=1)
    accent=[(229,177,80),(67,211,188),(97,185,249),(253,157,93),(168,151,255),(109,211,159),(227,174,94)][i]
    d.ellipse((350,-200,1100,550),fill=(18,40,54))
    d.rectangle((0,0,11,H),fill=accent)
    d.text((44,58),"老陳分享   /   OPEN SOURCE PICKS",font=font(24,True),fill=(192,210,226))
    d.text((44,118),sec+"   ·   2026",font=font(25),fill=accent)
    titlefont=font(67 if len(name)<16 else 52,True)
    titlelines=textwrap_px(name,titlefont,632)
    for j,l in enumerate(titlelines[:2]):d.text((44,205+j*80),l,font=titlefont,fill=(250,250,251))
    ypos=214+80*len(titlelines)+15
    for j,l in enumerate(textwrap_px(desc,font(27,True),614)[:2]):
        d.text((45,ypos+j*38),l,font=font(27,True),fill=accent)
    sy=410
    rr(d,(37,sy,682,890),(27,38,54),28,outline=(60,79,93))
    if shot and os.path.isfile(shot):
        try:
            ui=Image.open(shot).convert("RGB")
            sw,sh=ui.size
            # GitHub screenshot shown as an actual repository web page, never a fake app UI
            scale=min(610/sw,410/sh)
            w,h=int(sw*scale),int(sh*scale)
            ui=ui.resize((w,h),Image.Resampling.LANCZOS)
            im.paste(ui,(int(360-w/2),sy+38))
            d.text((60,850),"GITHUB 專案頁面實拍",font=font(19),fill=(165,190,205))
        except Exception:shot=None
    if not shot:
        # Fallback is an explicitly labeled informational card, not a fictional product UI
        d.text((65,467),"GITHUB   /   VERIFIED REPO",font=font(22),fill=accent)
        d.text((65,552),name,font=font(47,True),fill=(245,247,249))
        for j,l in enumerate(textwrap_px(repo or "開源軟體精選",font(25),530)):
            d.text((65,641+j*39),l,font=font(25),fill=(185,203,218))
        d.text((65,819),"官方專案資料｜非操作介面",font=font(20),fill=(155,180,197))
    d.text((44,934),"使用建議",font=font(23),fill=accent)
    excerpt=TC.convert(script)
    parts=textwrap_px(excerpt,font(25),615)
    for j,l in enumerate(parts[:6]):d.text((44,980+j*39),l,font=font(25),fill=(228,232,240))
    d.text((44,1190),"github.com/"+repo if repo else "老陳分享  ·  繁體中文字幕",
            font=font(21),fill=(143,163,185))
    outfile=P/f"frame_{i:02d}.png";im.save(outfile,optimize=True)
    return outfile
def run(cmd):
    subprocess.run(cmd,check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
def dur(p):
    z=subprocess.check_output(["ffprobe","-v","error","-show_entries","format=duration","-of","default=noprint_wrappers=1:nokey=1",str(p)]).decode()
    return float(z)
def tts(row,i):
    out=P/f"voice_{i:02d}.mp3";script=row[1]
    payload={"input":script,"voice":VOICE,"speed":1.0,"pitch":"-3","style":"general","volume":"0"}
    try:
        r=requests.post("https://tts.wangwangit.com/v1/audio/speech",json=payload,timeout=55)
        if r.ok and len(r.content)>800 and (r.headers.get("Content-Type","").startswith("audio") or r.content[:3]==b"ID3" or r.content[:2] in (b"\xff\xfb",b"\xff\xf3")):
            out.write_bytes(r.content)
            if dur(out)>3:
                print("TTS website success",i,dur(out));return out,"VoiceCraft / YunzeNeural"
        print("site response",i,r.status_code,r.text[:130])
    except Exception as e:print("site unavailable",i,str(e)[:180])
    # Same Microsoft voice ID, independent endpoint if the site is not reachable.
    import asyncio,edge_tts
    async def make():
        communicator=edge_tts.Communicate(script,VOICE,rate="+0%",pitch="-3Hz")
        await communicator.save(str(out))
    asyncio.run(make())
    if dur(out)<=3:raise RuntimeError("TTS returned invalid audio")
    print("TTS direct Edge success",i,dur(out))
    return out,"Microsoft Edge / YunzeNeural"
def get_screenshots():
    shots={}
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            browser=p.chromium.launch(headless=True,args=["--no-sandbox"])
            page=browser.new_page(viewport={"width":1120,"height":820},device_scale_factor=1)
            for i,row in enumerate(SEGS):
                if not row[4]:continue
                try:
                    page.goto("https://github.com/"+row[4],wait_until="domcontentloaded",timeout=25000)
                    page.wait_for_timeout(1000)
                    if page.title() and not "404" in page.title():
                        shot=P/f"shot_{i:02d}.png"
                        page.screenshot(path=str(shot))
                        shots[i]=str(shot)
                        print("Screenshot",i,page.title()[:50])
                except Exception as e:print("Screenshot skipped",i,str(e)[:120])
            browser.close()
    except Exception as e:print("Playwright not available:",e)
    return shots
def srt_time(t):
    ms=round(t*1000);hours,ms=divmod(ms,3600000);minutes,ms=divmod(ms,60000);secs,ms=divmod(ms,1000)
    return f"{hours:02}:{minutes:02}:{secs:02},{ms:03}"
def captions(text,start,length):
    # Split Chinese lines at punctuation for legibility
    parts=[s.strip() for s in re.split(r"(?<=[。！？；])",TC.convert(text)) if s.strip()]
    if len(parts)<2:
        parts=textwrap_px(TC.convert(text),font(22),500)
    total=sum(max(1,len(x)) for x in parts);t=start;rows=[]
    for p in parts:
        d=length*max(1,len(p))/total
        rows.append((t,t+d,p));t+=d
    return rows
def main():
    report=[]
    for i,row in enumerate(SEGS):
        p,provider=tts(row,i)
        report.append({"index":i,"voice":provider,"duration":dur(p),"text":row[1],"repo":row[4]})
    if len({x["voice"] for x in report})>1:
        raise RuntimeError("Mixed voice providers: abort to preserve consistent performance")
    shots=get_screenshots()
    # Generate scene images and concatenate short H.264 cuts
    concat=[];timeline=[];t=0.0
    for i,row in enumerate(SEGS):
        card=render_card(i,row,shots.get(i))
        length=report[i]["duration"]+0.55
        cut=P/f"clip_{i:02d}.mp4"
        # Real video file: visual scenes with gradual framing shifts and source page capture.
        frames=math.ceil(length*24)
        run(["ffmpeg","-y","-hide_banner","-loglevel","error","-loop","1","-i",str(card),
             "-vf",f"zoompan=z='min(zoom+0.00018,1.05)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s=720x1280:fps=24,format=yuv420p",
             "-frames:v",str(frames),"-c:v","libx264","-preset","veryfast","-crf","25","-r","24","-an",str(cut)])
        concat.append(cut)
        timeline.extend(captions(row[1],t,report[i]["duration"]))
        t+=length
    subtitle=P/"繁體字幕.srt"
    subtitle.write_text("\n\n".join(f"{j}\n{srt_time(a)} --> {srt_time(b)}\n{line}" for j,(a,b,line) in enumerate(timeline,1)),encoding="utf-8")
    (P/"繁體口播稿.txt").write_text("\n\n".join(TC.convert(x[1]) for x in SEGS),encoding="utf-8")
    (P/"簡體口播稿.txt").write_text("\n\n".join(x[1] for x in SEGS),encoding="utf-8")
    (P/"來源清單.md").write_text("# 老陈分享：五款 GitHub 开源软件\n\n"+
        "\n".join(f"- [{x[3]}](https://github.com/{x[4]})" for x in SEGS if x[4])+
        "\n\n画面取自相应公开 GitHub 仓库页面的编辑性截图；不代表已运行演示。"
        "\nStirling PDF 现为 open-core，需要分别核对功能条款。"
        "\n云泽配音为微软合成语音；目标网站声明仅供个人研究及非商业用途，商业化前需确认授权。\n",encoding="utf-8")
    audio=AudioSegment.empty()
    for i,row in enumerate(SEGS):
        audio+=AudioSegment.from_file(P/f"voice_{i:02d}.mp3")+AudioSegment.silent(duration=550)
    audio.export(P/"云泽配音.mp3",format="mp3",bitrate="128k")
    (P/"list.txt").write_text("".join("file '"+x.name+"'\n" for x in concat))
    run(["ffmpeg","-hide_banner","-loglevel","error","-y","-f","concat","-safe","0","-i",str(P/"list.txt"),"-c","copy",str(P/"video_noaudio.mp4")])
    # Subs internal mux avoids font rendering surprises; burned-in optional.
    base=P/"短视频_5款GitHub开源神器.mp4"
    run(["ffmpeg","-y","-hide_banner","-loglevel","error",
         "-i",str(P/"video_noaudio.mp4"),"-i",str(P/"云泽配音.mp3"),
         "-vf",f"subtitles={subtitle}:force_style='FontName=Noto Sans CJK TC,FontSize=17,PrimaryColour=&H00FFFFFF,OutlineColour=&HBB000000,BorderStyle=1,Outline=2,MarginV=75,Alignment=2'",
         "-map","0:v:0","-map","1:a:0","-c:v","libx264","-preset","veryfast","-crf","25","-c:a","aac","-b:a","128k","-movflags","+faststart","-shortest",str(base)])
    run(["ffmpeg","-hide_banner","-loglevel","error","-y","-i",str(base),"-frames:v","1","-update","1",str(P/"封面.jpg")])
    reportdict={"duration_seconds":dur(base),"voiced_by":report[0]["voice"],"original_voice_id":VOICE,"scenes":report,"filesize_bytes":base.stat().st_size}
    (P/"制作核验.json").write_text(json.dumps(reportdict,ensure_ascii=False,indent=2),encoding="utf-8")
    print("SUCCESS",json.dumps({"duration":dur(base),"bytes":base.stat().st_size,"source":report[0]["voice"]}))
    if not 120 <= dur(base) <= 199:
        print("WARN: target 2+ minutes check",dur(base))
if __name__=="__main__":main()
