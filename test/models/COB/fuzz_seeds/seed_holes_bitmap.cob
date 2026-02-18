Caligari V00.01ALH             
Grou V0.01 Id 1 Parent 0 Size 00000137
Name SceneRoot
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
Units 3
Grou V0.01 Id 3 Parent 1 Size 00000137
Name SubGroup
center 0 0 0
x axis 1 0 0
y axis 0 1 0
z axis 0 0 1
Transform
0.5 0 0 2
0 0.5 0 0
0 0 0.5 0
0 0 0 1
PolH V0.08 Id 10 Parent 3 Size 00013948
Name Pyramid
center 0 0 0
x axis 1 0 0
y axis 0 1 0
z axis 0 0 1
Transform
2 0 0 0
0 2 0 0
0 0 2 0
0 0 0 1
World Vertices 8
-2.000000 0.000000 -2.000000
2.000000 0.000000 -2.000000
2.000000 0.000000 2.000000
-2.000000 0.000000 2.000000
-1.000000 1.000000 0.000000
1.000000 1.000000 0.000000
0.000000 1.000000 1.000000
0.000000 2.000000 0.000000
Texture Vertices 8
0.000000 0.000000
1.000000 0.000000
1.000000 1.000000
0.000000 1.000000
0.100000 0.500000
0.900000 0.500000
0.500000 0.900000
0.500000 0.500000
Faces 6
Face verts 4 flags 0 mat 0
 <0,0> <1,1> <2,2> <3,3>
Face verts 3 flags 0 mat 1
 <4,4> <5,5> <6,6>
Face verts 3 flags 0 mat 1
 <4,4> <6,6> <7,7>
Face verts 3 flags 0 mat 1
 <5,5> <6,6> <7,7>
Face verts 3 flags 0 mat 0
 <0,0> <4,4> <1,1>
Face verts 3 flags 0 mat 0
 <2,2> <6,6> <3,3>
DrawFlags 1
Mat1 V0.08 Id 15 Parent 10 Size 00000200
mat# 0
shader: flat  facet: auto40
rgb 0.6,0.6,0.6
alpha 0.8  ka 0.3  ks 0.1  exp 8  ior 1
Mat1 V0.08 Id 16 Parent 10 Size 00000200
mat# 1
shader: metal  facet: auto40
rgb 0.9,0.8,0.2
alpha 1  ka 0.1  ks 0.8  exp 128  ior 2.5
Bone V0.05 Id 40 Parent 3 Size 00001000
Name SpineBone
center 0 1 0
x axis 1 0 0
y axis 0 1 0
z axis 0 0 1
Transform
1 0 0 0
0 1 0 1
0 0 1 0
0 0 0 1
END X
