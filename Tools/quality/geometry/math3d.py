"""Unreal Rotator transform math and floor sampling, independent of Unreal."""
import math

def rotate(v,rotation):
 p,y,r=map(math.radians,rotation);cp,sp,cy,sy,cr,sr=math.cos(p),math.sin(p),math.cos(y),math.sin(y),math.cos(r),math.sin(r)
 axes=((cp*cy,cp*sy,sp),(sr*sp*cy-cr*sy,sr*sp*sy+cr*cy,-sr*cp),(-cr*sp*cy-sr*sy,cy*sr-cr*sp*sy,cr*cp))
 return [sum(v[j]*axes[j][i]for j in range(3))for i in range(3)]
def position(v,record):return [a+b for a,b in zip(rotate([x*s for x,s in zip(v,record['scale'])],record['rotation']),record['location'])]
def normal(v,record):
 out=rotate([x/s for x,s in zip(v,record['scale'])],record['rotation']);length=math.sqrt(sum(x*x for x in out));return [x/length for x in out]if length else [0,0,0]
def triangle(a,b,c):
 u=[b[i]-a[i]for i in range(3)];v=[c[i]-a[i]for i in range(3)];cross=[u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0]];length=math.sqrt(sum(x*x for x in cross))
 return {'centroid':[sum(t[i]for t in (a,b,c))/3 for i in range(3)],'area':length/2,'normal':[x/length for x in cross]if length else [0,0,0]}
def slope_degrees(n):return math.degrees(math.acos(max(-1,min(1,n[2]))))
def passage_fits(width,radius,margin=4):return width>=2*(radius+margin)
