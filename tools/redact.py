"""Blur regions of a screenshot before using it in a video.
usage: python tools/redact.py in.png out.png x0,y0,x1,y1 [x0,y0,x1,y1 ...]   (pixel coords of in.png)"""
import sys
from PIL import Image,ImageFilter
im=Image.open(sys.argv[1]).convert('RGB')
for b in sys.argv[3:]:
    box=tuple(int(v) for v in b.split(',')); im.paste(im.crop(box).filter(ImageFilter.GaussianBlur(18)),box)
im.save(sys.argv[2])
