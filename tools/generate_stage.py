from PIL import Image, ImageDraw, ImageFont, ImageFilter
from pathlib import Path
import math, random
random.seed(26)
W,H=1600,900
out=Path(__file__).resolve().parents[1]/'assets'/'saigon-night.png'
im=Image.new('RGB',(W,H)); px=im.load()
for y in range(H):
    t=y/H
    for x in range(W):
        # deep blue / dark lilac ambient street light
        v=0.09*math.sin(x/155)+0.05*math.sin(x/71)
        px[x,y]=(max(0,int(10+20*t+v*18)),max(0,int(15+21*t)),max(0,int(35+36*(1-t))))
d=ImageDraw.Draw(im,'RGBA')
# soft atmospheric glows
halo=Image.new('RGBA',(W,H),(0,0,0,0)); g=ImageDraw.Draw(halo,'RGBA')
for cx,cy,rad,col in [(390,390,320,(255,96,57)),(1230,335,380,(210,42,145)),(810,235,400,(38,85,231)),(760,490,200,(10,199,250))]:
    g.ellipse((cx-rad,cy-rad,cx+rad,cy+rad),fill=(*col,120))
halo=halo.filter(ImageFilter.GaussianBlur(145));im=Image.alpha_composite(im.convert('RGBA'),halo)
d=ImageDraw.Draw(im,'RGBA')
# distant skyline and haze
for i in range(62):
    x=i*29-20
    height=random.randint(125,365)
    c=random.choice([(15,20,37,255),(20,25,45,255),(19,20,40,255)])
    d.rectangle((x,520-height,x+random.randint(23,65),550),fill=c)
    for yy in range(530-height,535,28):
        for xx in range(x+6,x+40,13):
            if random.random()<0.27: d.rectangle((xx,yy,xx+4,yy+8),fill=(244,146,88,70))
# street recedes to narrow central opening; adjacent buildings facades
# wall left
left_poly=[(0,70),(265,95),(397,290),(537,540),(0,610)]
d.polygon(left_poly, fill=(27,22,37,255))
d.line([(0,70),(265,95),(397,290),(537,540)],fill=(68,54,76,255),width=9)
right_poly=[(1600,56),(1335,110),(1215,270),(1053,545),(1600,600)]
d.polygon(right_poly,fill=(33,25,46,255))
d.line([(1600,56),(1335,110),(1215,270),(1053,545)],fill=(70,46,72,255),width=9)
# masonry lines and vertical facade pillars
for side in ('L','R'):
    for k in range(6):
        if side=='L':
            xa=k*92-24; ya=160+k*36; xb=xa+66; yb=600-k*7
        else:
            xa=W-k*93+15; ya=160+k*32; xb=xa-72; yb=599-k*7
        d.line((xa,ya,xb,yb),fill=(0,0,0,95),width=7)
        d.line((xa+6,ya+3,xb+6,yb),fill=(122,91,105,32),width=3)
    for yy in range(245,540,66):
        d.line((0,yy,390,yy+13),fill=(130,83,86,35),width=3)
        d.line((1200,yy+12,1600,yy),fill=(130,83,86,35),width=3)
# vibrant shop awnings/storefront on sides
for side in ('L','R'):
    if side=='L':
        positions=[(0,373,212,562),(215,420,393,573),(400,479,520,580)]
    else:
        positions=[(1380,372,1600,563),(1192,423,1394,575),(1072,482,1199,578)]
    for j,(x0,y0,x1,y1) in enumerate(positions):
        tint=[(255,132,72),(46,185,250),(240,67,141)][j]
        d.rectangle((x0,y0,x1,y1),fill=(21,19,27,255),outline=(*tint,110),width=3)
        d.polygon([(x0-8,y0),(x1+8,y0),(x1+20,y0+34),(x0-15,y0+34)],fill=(*tint,115))
        for n in range(3):
            x=x0+12+n*max(30,(x1-x0-24)//3)
            d.rectangle((x,y0+40,x+24,y1-4),fill=(246,173,90,45),outline=(243,167,85,65),width=2)
# fluorescent sign boxes
def neon_rect(box,color,fill=(19,16,29,235)):
    x0,y0,x1,y1=box
    for w,alpha in [(20,12),(11,22),(5,65)]:
        d.rounded_rectangle((x0-w,y0-w,x1+w,y1+w),radius=5,outline=(*color,alpha),width=max(1,w//2))
    d.rounded_rectangle(box,radius=4,fill=fill,outline=(*color,235),width=4)
try:
    bold='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
    title_font=ImageFont.truetype(bold,35)
    med_font=ImageFont.truetype(bold,28)
except: title_font=med_font=None
for box,color,label,font in [
    ((40,250,268,320),(255,97,62),'BIA HƠI',title_font),
    ((1290,244,1558,317),(242,65,133),'HẺM CHIẾN',med_font),
    ((334,332,471,387),(55,211,245),'CÀ PHÊ',med_font),
    ((1151,338,1352,399),(255,171,67),'CƠM TẤM',med_font),
    ((675,214,946,268),(91,167,245),'SÀI GÒN',title_font),
]:
    neon_rect(box,color)
    x0,y0,x1,y1=box
    if font: 
        bb=d.textbbox((0,0),label,font=font)
        tw=bb[2]-bb[0];th=bb[3]-bb[1]
        d.text(((x0+x1-tw)/2,(y0+y1-th)/2-5),label,font=font,fill=(*color,255))
# overhead cable silhouettes
for yy in (98,151,180,265,310):
    pts=[]
    for x in range(-20,W+20,30): pts.append((x,int(yy+36*math.sin(math.pi*x/W))))
    d.line(pts,fill=(9,10,19,240),width=random.randint(3,6))
for x in (130,372,663,1013,1228,1488):
    d.line((x,0,x+random.randint(-20,20),random.randint(100,200)),fill=(15,12,24,225),width=4)
# hanging lamps
for x,y,c in [(303,320,(255,153,70)),(1192,303,(250,109,87)),(850,360,(255,170,95))]:
    rad=20
    d.line((x,y-55,x,y-8),fill=(26,22,29,250),width=3)
    d.ellipse((x-rad,y-rad//2,x+rad,y+rad//2),fill=(*c,240))
    d.ellipse((x-56,y-52,x+56,y+52),fill=(*c,20))
# silhouettes spectators behind playfield
for x in [78,151,261,324,475,552,1056,1152,1297,1392,1510]:
    y=520+random.randint(-4,27); sc=random.uniform(.65,1.1); head=12*sc
    c=random.choice([(10,15,26,255),(13,18,31,255),(18,17,26,255)])
    d.ellipse((x-head,y-86*sc-head,x+head,y-86*sc+head),fill=c)
    d.polygon([(x-14*sc,y-69*sc),(x+16*sc,y-69*sc),(x+19*sc,y-5),(x-23*sc,y-4)],fill=c)
    d.line((x-10*sc,y-12,x-16*sc,y+18),fill=c,width=9)
    d.line((x+9*sc,y-12,x+15*sc,y+18),fill=c,width=9)
# storefront barrels, red plastic stools
for x,y in [(137,571),(182,580),(258,572),(1333,579),(1450,581)]:
    d.rectangle((x,y-14,x+36,y-3),fill=(171,48,53,235))
    d.line((x+6,y-4,x+3,y+20),fill=(145,39,49,245),width=5)
    d.line((x+30,y-4,x+32,y+20),fill=(145,39,49,245),width=5)
# deep dark asphalt; rainy reflective street
road_top=556
d.polygon([(0,road_top),(W,road_top),(W,H),(0,H)],fill=(16,20,33,255))
# street perspective grout
for x in (0,200,430,820,1170,1510):
    d.line((800+(x-800)*0.11,555,x,900),fill=(68,66,80,55),width=3)
for y in (598,661,737,826): d.line((0,y,W,y),fill=(85,74,87,28),width=2)
# water pools neon streaks
for i in range(350):
    x=random.randint(0,W); y=random.randint(587,H)
    yf=(y-road_top)/(H-road_top)
    ln=random.randint(10,74) * (0.3+yf)
    if x<570: col=random.choice([(255,99,63),(239,135,73),(237,62,117)])
    elif x>1100: col=random.choice([(238,67,156),(255,160,71),(69,117,246)])
    else: col=random.choice([(45,158,231),(235,114,139),(245,176,93)])
    d.line((x,y,x+ln,y+random.randint(-2,2)),fill=(*col,random.randint(25,145)),width=random.choice([1,2,3,4]))
# long vertical water reflections under signs
for sx,c in [(160,(252,113,57)),(399,(28,170,249)),(1280,(231,57,142)),(846,(58,122,237))]:
    for i in range(85):
        yy=random.randint(575,899)
        reach=(yy-565)/350
        xx=sx+random.gauss(0,18+reach*78)
        ln=random.randint(6,36+int(reach*36))
        d.line((xx,yy,xx+ln,yy),fill=(*c,random.randint(20,90)),width=random.randint(1,4))
# raindrops faint fine points
for i in range(400):
    x=random.randint(0,W);y=random.randint(20,720)
    d.line((x,y,x-3,y+random.randint(7,17)),fill=(132,175,215,random.randint(10,38)),width=1)
# stage-ground highlight under feet
d.line((0,619,W,619),fill=(218,185,173,20),width=2)
# cinematic vignette overlay
vig=Image.new('RGBA',(W,H),(0,0,0,0));v=ImageDraw.Draw(vig,'RGBA')
for i in range(42):
    alpha=int(3+16*i/42)
    v.rectangle((i*4,i*2,W-i*4,H-i*2),outline=(1,1,8,alpha),width=7)
im=Image.alpha_composite(im,vig).convert('RGB')
im.save(out,quality=95)
print(out, im.size)
