"""Render a kanban/board image (design-system dark style) from a JSON list of cards.
usage: python tools/board.py board.example.json shots/board.png
card fields: Name, Type (column), Status, Line, Focus"""
import json,sys,os,textwrap
from PIL import Image,ImageDraw,ImageFont
CFG=json.load(open(os.environ.get('RVG_CONFIG','config.json')))
rows=json.load(open(sys.argv[1])); out=sys.argv[2]
f=lambda p,s:ImageFont.truetype(CFG[p],s,index=0)
title=os.environ.get('BOARD_TITLE','Fleet Board')
types=list(dict.fromkeys(r['Type'] for r in rows))
W,H=1400,820; im=Image.new('RGB',(W,H),(13,15,18)); d=ImageDraw.Draw(im)
d.text((40,30),title,font=f('font_jp_bold',44),fill=(245,245,240))
col={'Green':(16,185,129),'Yellow':(245,158,11),'Blocked':(239,68,68),'Red':(239,68,68),'Open':(6,182,212)}
n=len(types); cw=(W-80-(n-1)*20)//n
for i,t in enumerate(types):
    x=40+i*(cw+20); d.rounded_rectangle((x,150,x+cw,H-40),16,fill=(15,23,42))
    items=[r for r in rows if r['Type']==t]; d.text((x+20,166),f'{t}  {len(items)}',font=f('font_jp_bold',26),fill=(203,213,225)); y=220
    for r in items:
        lines=textwrap.wrap(r.get('Focus',''),24)[:3]; h=110+len(lines)*30
        d.rounded_rectangle((x+14,y,x+cw-14,y+h),16,fill=(30,41,59),outline=(71,85,105),width=2)
        d.text((x+32,y+16),textwrap.shorten(r['Name'],22,placeholder='…'),font=f('font_jp_bold',24),fill=(245,245,240))
        st=r.get('Status',''); c=col.get(st,(148,163,184))
        d.rounded_rectangle((x+32,y+56,x+52+13*len(st),y+88),16,fill=tuple(v*3//10 for v in c),outline=c); d.text((x+42,y+59),st,font=f('font_jp_bold',20),fill=c)
        d.text((x+64+13*len(st),y+60),r.get('Line',''),font=f('font_jp_regular',20),fill=(148,163,184))
        for k,l in enumerate(lines): d.text((x+32,y+100+k*30),l,font=f('font_jp_regular',21),fill=(203,213,225))
        y+=h+16
os.makedirs(os.path.dirname(out) or '.',exist_ok=True); im.save(out)
