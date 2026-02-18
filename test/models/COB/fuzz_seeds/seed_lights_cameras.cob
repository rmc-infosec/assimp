Caligari V00.01ALH
Grou V0.01 Id 1 Parent 0 Size 00000137
Name Scene
center 0 0 0
x axis 1 0 0
y axis 0 1 0
z axis 0 0 1
Transform
1 0 0 0
0 1 0 0
0 0 1 0
0 0 0 1
Unit V0.01 Id 2 Parent 1 Size 00000009
Units 0
PolH V0.08 Id 5 Parent 1 Size 00005000
Name Ground
center 0 0 0
x axis 1 0 0
y axis 0 1 0
z axis 0 0 1
Transform
1 0 0 0
0 1 0 0
0 0 1 0
0 0 0 1
World Vertices 4
-10.000000 0.000000 -10.000000
10.000000 0.000000 -10.000000
10.000000 0.000000 10.000000
-10.000000 0.000000 10.000000
Texture Vertices 4
0.000000 0.000000
1.000000 0.000000
1.000000 1.000000
0.000000 1.000000
Faces 2
Face verts 3 flags 0 mat 0
 <0,0> <1,1> <2,2>
Face verts 3 flags 0 mat 0
 <0,0> <2,2> <3,3>
DrawFlags 0
Mat1 V0.08 Id 6 Parent 5 Size 00000200
mat# 0
shader: phong  facet: auto40
rgb 0.7,0.7,0.7
alpha 1  ka 0.2  ks 0.3  exp 32  ior 1
Lght V0.08 Id 10 Parent 1 Size 00001000
Name SpotLight1
center 5 8 5
x axis 0.707 0 -0.707
y axis 0 1 0
z axis 0.707 0 0.707
Transform
0.707 0 -0.707 5
0 1 0 8
0.707 0 0.707 5
0 0 0 1
Spot color 1.0,0.95,0.8 cone angle 35 inner angle 20
Lght V0.08 Id 11 Parent 1 Size 00001000
Name InfiniteLight
center 0 20 0
x axis 1 0 0
y axis 0 1 0
z axis 0 0 1
Transform
1 0 0 0
0 1 0 20
0 0 1 0
0 0 0 1
Infinite color 0.4,0.4,0.5 cone angle 180 inner angle 180
Lght V0.08 Id 12 Parent 1 Size 00001000
Name LocalLight
center -3 4 -3
x axis 1 0 0
y axis 0 1 0
z axis 0 0 1
Transform
1 0 0 -3
0 1 0 4
0 0 1 -3
0 0 0 1
Local color 0.9,0.6,0.3 cone angle 90 inner angle 60
Came V0.02 Id 20 Parent 1 Size 00001000
Name MainCamera
center 0 5 15
x axis 1 0 0
y axis 0 1 0
z axis 0 0 1
Transform
1 0 0 0
0 1 0 5
0 0 1 15
0 0 0 1
Standard
Came V0.02 Id 21 Parent 1 Size 00001000
Name TopCamera
center 0 20 0
x axis 1 0 0
y axis 0 0 1
z axis 0 -1 0
Transform
1 0 0 0
0 0 1 20
0 -1 0 0
0 0 0 1
Panoramic
Chan V0.08 Id 30 Parent 10 Size 00000100
END X
