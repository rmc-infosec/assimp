Caligari V00.01ALH
Grou V0.01 Id 1 Parent 0 Size 00000137
Name Root
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
Units 5
PolH V0.08 Id 10 Parent 1 Size 00005000
Name FeetMesh
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
-1 0 -1
1 0 -1
1 0 1
-1 0 1
Texture Vertices 4
0 0
1 0
1 1
0 1
Faces 2
Face verts 3 flags 0 mat 0
 <0,0> <1,1> <2,2>
Face verts 3 flags 0 mat 0
 <0,0> <2,2> <3,3>
DrawFlags 2
Mat1 V0.08 Id 11 Parent 10 Size 00000200
mat# 0
shader: phong  facet: smooth
rgb 0.5,0.5,0.5
alpha 0.5  ka 0.3  ks 0.7  exp 128  ior 1.5
Lght V0.08 Id 20 Parent 1 Size 00000200
Name SpotLight
center 0 5 0
x axis 1 0 0
y axis 0 1 0
z axis 0 0 1
Transform
1 0 0 0
0 1 0 5
0 0 1 0
0 0 0 1
Came V0.02 Id 30 Parent 1 Size 00000200
Name MainCam
center 0 3 10
x axis 1 0 0
y axis 0 1 0
z axis 0 0 1
Transform
1 0 0 0
0 1 0 3
0 0 1 10
0 0 0 1
END X
