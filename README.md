# SpineAtlas
Modify atlas data and export frames or convert other atlas-like data to spine atlas

## Installation
Install the latest version of `SpineAtlas` from PyPI:

```bash
pip install SpineAtlas
```

## Usage
# Opening and saving atlas
```python
from SpineAtlas import ReadAtlasFile

atlas = ReadAtlasFile('1.atlas')
# The code will automatically determine the format of Atlas
atlas.version = False # Convert to Atlas 3.0 format
atlas.version = True # Convert to Atlas 4.0 format
atlas.SaveAtlas('1_v4.atlas')
```
# Check if the atlas is missing a textures
```python
from SpineAtlas import ReadAtlasFile

atlas = ReadAtlasFile('1.atlas')
# If the texture and atlas are in the same directory, you don't need to pass the path
miss = atlas.CheckTextures()
# If `miss` is empty, it means there is no missing textures
```
# Modify the texture scaling of the atlas
```python
from SpineAtlas import ReadAtlasFile

atlas = ReadAtlasFile('1.atlas')
# If the texture and atlas are in the same directory, you don't need to pass the path
atlas.ReScale()
atlas.SaveAtlas('1_scale.atlas')

# Atlas4.0
atlas = ReadAtlasFile('1.atlas')
atlas.version = False # If you want to save it as Atlas3.0
atlas.SaveAtlas4_0Scale(outPath=r'D:\out_scale')
```
# Export atlas frames
```python
from SpineAtlas import ReadAtlasFile

atlas = ReadAtlasFile('1.atlas')
# If the texture and atlas are in the same directory, you don't need to pass the texture path
# mode : ['Normal', 'Premul', 'NonPremul']
# --- Normal - do not process the texture
# --- Premul - convert the texture to premultiplied
# --- NonPremul - convert the texture to non-premultiplied
atlas.SaveFrames(path='1_frames', mode='Premul')
```
# Convert other formats to `Spine Atlas`
```python
from SpineAtlas import Atlas, AtlasTex, AtlasFrame

'''
{
Texture:
    Texture_Name: str
    Texture_Wdith: int
    Texture_Height: int
	
Frame:
[
    [
    Frame_Name: str
    Cut_X: int
    Cut_Y: int
    Cut_Wdith: int
    Cut_Height: int
    Original_X: int
    Original_Y: int
    Original_Wdith: int
    Original_Height: int
    Rotate: int
    ],
    ...
]
}
'''
TextureDict = {...}
frames = []
for i in TextureDict['Frame']:
    frames.append(AtlasFrame(i['Frame_Name'], i['Cut_X'], i['Cut_Y'], i['Cut_Wdith'], i['Cut_Height'], i['Original_X'], i['Original_Y'], i['Original_Wdith'], i['Original_Height'], i['Rotate']))
tex = TextureDict['Texture']
texture = AtlasTex(tex['Texture_Name'], tex['Texture_Wdith'], tex['Texture_Height'], frames=frames)
atlas = Atlas([texture])
atlas.SaveAtlas('1.atlas')
```
# Recalculate the clipping anchor point
```python
from SpineAtlas import ReadAtlasFile, Anchor

'''
class Anchor(IntEnum):
    TOP_LEFT = 1
    TOP_CENTER = 2
    TOP_RIGHT = 3
    CENTER_LEFT = 4
    CENTER = 5
    CENTER_RIGHT = 6
    BOTTOM_LEFT = 7
    BOTTOM_CENTER = 8
    BOTTOM_RIGHT = 9
'''

atlas = ReadAtlasFile('1.atlas')
# The default anchor point for Spine Atlas clipping is the top left corner
atlas.cutp = Anchor.BOTTOM_LEFT
atlas.ReOffset() # Recalculate clipping X/Y starting from the upper left corner
atlas.SaveAtlas('1_1_ReOffset.atlas')
```
# Recalculate the Offset anchor point
```python
from SpineAtlas import ReadAtlasFile, Anchor

'''
class Anchor(IntEnum):
    TOP_LEFT = 1
    TOP_CENTER = 2
    TOP_RIGHT = 3
    CENTER_LEFT = 4
    CENTER = 5
    CENTER_RIGHT = 6
    BOTTOM_LEFT = 7
    BOTTOM_CENTER = 8
    BOTTOM_RIGHT = 9
'''

atlas = ReadAtlasFile('1.atlas')
# The default anchor point for Spine Atlas Offset is the bottom left corner
atlas.offp = Anchor.TOP_LEFT
atlas.ReOffset() # Recalculate Offset X/Y starting from the bottom left corner
atlas.SaveAtlas('1_1_ReOffset.atlas')
```
# Convert image to premultiplied/non-premultiplied
```python
from PIL.Image import open as imgop
from SpineAtlas import ImgPremultiplied, ImgNonPremultiplied

img = imgop('1.png')

tex = ImgPremultiplied(img)
tex.save('1_premultiplied.png')

tex = ImgNonPremultiplied(img)
tex.save('1_non-premultiplied.png')
```
