textures/test/material1
{
    cull none
    {
        map textures/test/diffuse.tga
        blendfunc add
        alphaFunc GT0
    }
    {
        map $lightmap
        blendfunc filter
    }
}
textures/test/material2
{
    cull twosided
    {
        map textures/test/glow.tga
        blendfunc blend
        alphaFunc GE128
    }
}
textures/test/material3
{
    cull back
    {
        map textures/test/alpha.tga
        blendfunc GL_SRC_ALPHA GL_ONE_MINUS_SRC_ALPHA
        alphaFunc LT128
    }
    {
        map textures/test/normal.tga
        blendfunc GL_ONE GL_ONE
    }
}
