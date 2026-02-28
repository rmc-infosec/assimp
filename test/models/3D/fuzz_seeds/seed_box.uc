class seed_box expands Actor;

#exec MESH IMPORT MESH=seed_box ANIVFILE=MODELS\seed_box_a.3d DATAFILE=MODELS\seed_box_d.3d X=0 Y=0 Z=0
#exec MESH ORIGIN MESH=seed_box X=0 Y=0 Z=0

#exec MESH SEQUENCE MESH=seed_box SEQ=All STARTFRAME=0 NUMFRAMES=3

#exec MESHMAP NEW MESHMAP=seed_box MESH=seed_box
#exec MESHMAP SCALE MESHMAP=seed_box X=0.1 Y=0.1 Z=0.2

#exec TEXTURE IMPORT NAME=BodyTex FILE=body.pcx GROUP=Skins FLAGS=2
#exec TEXTURE IMPORT NAME=BodyTex FILE=body.pcx GROUP=Skins PALETTE=BodyTex
#exec MESHMAP SETTEXTURE MESHMAP=seed_box NUM=0 TEXTURE=BodyTex

#exec TEXTURE IMPORT NAME=WeaponTex FILE=weapon.pcx GROUP=Skins FLAGS=2
#exec TEXTURE IMPORT NAME=WeaponTex FILE=weapon.pcx GROUP=Skins PALETTE=WeaponTex
#exec MESHMAP SETTEXTURE MESHMAP=seed_box NUM=1 TEXTURE=WeaponTex

defaultproperties
{
    DrawType=DT_Mesh
    Mesh=seed_box
}
