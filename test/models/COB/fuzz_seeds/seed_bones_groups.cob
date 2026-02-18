Caligari V00.01ALH
Grou V0.01 Id 1 Parent 0 Size 00000137
Name RootGroup
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
Grou V0.01 Id 10 Parent 1 Size 00000137
Name BodyGroup
center 0 0 0
x axis 1 0 0
y axis 0 1 0
z axis 0 0 1
Transform
1 0 0 0
0 1 0 0
0 0 1 0
0 0 0 1
PolH V0.08 Id 20 Parent 10 Size 00005000
Name Torso
center 0 0 0
x axis 1 0 0
y axis 0 1 0
z axis 0 0 1
Transform
1 0 0 0
0 1 0 0
0 0 1 0
0 0 0 1
World Vertices 6
-0.500000 0.000000 0.000000
0.500000 0.000000 0.000000
0.500000 2.000000 0.000000
-0.500000 2.000000 0.000000
0.000000 0.000000 0.500000
0.000000 2.000000 0.500000
Texture Vertices 6
0.000000 0.000000
1.000000 0.000000
1.000000 1.000000
0.000000 1.000000
0.500000 0.000000
0.500000 1.000000
Faces 4
Face verts 3 flags 0 mat 0
 <0,0> <1,1> <2,2>
Face verts 3 flags 0 mat 0
 <0,0> <2,2> <3,3>
Face verts 3 flags 0 mat 1
 <0,0> <4,4> <1,1>
Face verts 3 flags 0 mat 1
 <3,3> <5,5> <2,2>
DrawFlags 0
Mat1 V0.08 Id 25 Parent 20 Size 00000200
mat# 0
shader: phong  facet: auto40
rgb 0.8,0.6,0.5
alpha 1  ka 0.2  ks 0.3  exp 32  ior 1
Mat1 V0.08 Id 26 Parent 20 Size 00000200
mat# 1
shader: metal  facet: auto40
rgb 0.3,0.3,0.8
alpha 1  ka 0.1  ks 0.6  exp 64  ior 1.2
PolH V0.04 Id 21 Parent 10 Size 00005000
Name Head
center 0 2.5 0
x axis 1 0 0
y axis 0 1 0
z axis 0 0 1
Transform
0.5 0 0 0
0 0.5 0 2.5
0 0 0.5 0
0 0 0 1
World Vertices 4
-1.000000 0.000000 0.000000
1.000000 0.000000 0.000000
1.000000 1.000000 0.000000
-1.000000 1.000000 0.000000
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
Grou V0.01 Id 30 Parent 1 Size 00000137
Name ArmGroup
center 0 0 0
x axis 1 0 0
y axis 0 1 0
z axis 0 0 1
Transform
1 0 0 0
0 1 0 0
0 0 1 0
0 0 0 1
Bone V0.05 Id 40 Parent 10 Size 00001000
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
Bone V0.05 Id 41 Parent 40 Size 00001000
Name NeckBone
center 0 2 0
x axis 1 0 0
y axis 0 1 0
z axis 0 0 1
Transform
1 0 0 0
0 1 0 2
0 0 1 0
0 0 0 1
Bone V0.05 Id 42 Parent 30 Size 00001000
Name ArmBone_L
center -1 1.5 0
x axis 1 0 0
y axis 0 1 0
z axis 0 0 1
Transform
1 0 0 -1
0 1 0 1.5
0 0 1 0
0 0 0 1
Bone V0.05 Id 43 Parent 30 Size 00001000
Name ArmBone_R
center 1 1.5 0
x axis 1 0 0
y axis 0 1 0
z axis 0 0 1
Transform
1 0 0 1
0 1 0 1.5
0 0 1 0
0 0 0 1
Chan V0.08 Id 50 Parent 40 Size 00000100
Chan V0.08 Id 51 Parent 41 Size 00000100
END X
