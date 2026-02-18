Caligari V00.01ALH             
Grou V0.01 Id 1 Parent 0 Size 00000137
Name root
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
Units 2
PolH V0.04 Id 3 Parent 1 Size 00013948
Name ColorBox
center 0 0 0
x axis 1 0 0
y axis 0 1 0
z axis 0 0 1
Transform
1 0 0 0
0 1 0 0
0 0 1 0
0 0 0 1
World Vertices 8
-1.000000 -1.000000 -1.000000
1.000000 -1.000000 -1.000000
1.000000 1.000000 -1.000000
-1.000000 1.000000 -1.000000
-1.000000 -1.000000 1.000000
1.000000 -1.000000 1.000000
1.000000 1.000000 1.000000
-1.000000 1.000000 1.000000
Texture Vertices 4
0.000000 0.000000
1.000000 0.000000
1.000000 1.000000
0.000000 1.000000
Faces 6
Face verts 4 flags 0 mat 0
 <0,0> <1,1> <2,2> <3,3>
Face verts 4 flags 0 mat 0
 <4,0> <7,1> <6,2> <5,3>
Face verts 4 flags 0 mat 1
 <0,0> <4,1> <5,2> <1,3>
Face verts 4 flags 0 mat 1
 <2,0> <6,1> <7,2> <3,3>
Face verts 4 flags 0 mat 2
 <0,0> <3,1> <7,2> <4,3>
Face verts 4 flags 0 mat 2
 <1,0> <5,1> <6,2> <2,3>
Mat1 V0.08 Id 10 Parent 3 Size 00000200
mat# 0
shader: phong  facet: auto40
rgb 0.8,0.2,0.2
alpha 1  ka 0.1  ks 0.3  exp 32  ior 1
Mat1 V0.08 Id 11 Parent 3 Size 00000200
mat# 1
shader: metal  facet: auto40
rgb 0.2,0.8,0.2
alpha 1  ka 0.1  ks 0.5  exp 64  ior 1
Mat1 V0.08 Id 12 Parent 3 Size 00000200
mat# 2
shader: flat  facet: auto40
rgb 0.2,0.2,0.8
alpha 0.5  ka 0.2  ks 0.1  exp 16  ior 1.5
END X
