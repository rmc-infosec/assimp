class seed_alltypes expands Actor;

#exec MESH IMPORT MESH=seed_alltypes ANIVFILE=MODELS\seed_alltypes_a.3d DATAFILE=MODELS\seed_alltypes_d.3d X=0 Y=0 Z=0
#exec MESH ORIGIN MESH=seed_alltypes X=0 Y=0 Z=0

#exec MESH SEQUENCE MESH=seed_alltypes SEQ=All STARTFRAME=0 NUMFRAMES=2

#exec MESHMAP NEW MESHMAP=seed_alltypes MESH=seed_alltypes
#exec MESHMAP SCALE MESHMAP=seed_alltypes X=0.05 Y=0.05 Z=0.1

#exec TEXTURE IMPORT NAME=SkinTex FILE=skin.pcx GROUP=Skins FLAGS=2
#exec TEXTURE IMPORT NAME=SkinTex FILE=skin.pcx GROUP=Skins PALETTE=SkinTex
#exec MESHMAP SETTEXTURE MESHMAP=seed_alltypes NUM=0 TEXTURE=SkinTex

#exec TEXTURE IMPORT NAME=DetailTex FILE=detail.pcx GROUP=Skins FLAGS=2
#exec TEXTURE IMPORT NAME=DetailTex FILE=detail.pcx GROUP=Skins PALETTE=DetailTex
#exec MESHMAP SETTEXTURE MESHMAP=seed_alltypes NUM=1 TEXTURE=DetailTex

#exec TEXTURE IMPORT NAME=WeaponTex FILE=weapon.pcx GROUP=Skins FLAGS=2
#exec TEXTURE IMPORT NAME=WeaponTex FILE=weapon.pcx GROUP=Skins PALETTE=WeaponTex
#exec MESHMAP SETTEXTURE MESHMAP=seed_alltypes NUM=2 TEXTURE=WeaponTex

defaultproperties
{
    DrawType=DT_Mesh
    Mesh=seed_alltypes
}
