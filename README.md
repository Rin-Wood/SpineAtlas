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
from SpineAtlas import rbin, sline, SpineAtlas

data = rbin('1.atlas')
atlas_cls = SpineAtlas(data)
# version is bool, True is 4.x, False is 3.x
if atlas_cls.atlas.version:
    # if atlas version is 4.x, save 3.x
    atlas_cls.atlas.version = False
else:
    # if atlas version is 3.x, save 4.x
    atlas_cls.atlas.version = True
text = atlas_cls.atlas.ConvertText # List[str]
sline('1_mod.atlas', text)
```
# Modify the texture scaling of the atlas
```python
from SpineAtlas import rbin, sline, SpineAtlas, AtlasScale

data = rbin('1.atlas')
atlas_cls = SpineAtlas(data)
for i in atlas_cls.atlas.atlas:
    # Get the width/height of png
    png = rbin(i.png, 24)[16:]
    pwidth, pheight = int.from_bytes(png[:4], byteorder='big'), int.from_bytes(png[4:], byteorder='big')
    # Get the width/height of atlas
    width, height = i.w, i.h
    # Calculate scaling and modify
    wscale, hscale = pwidth / width, pheight / height
    AtlasScale(i, wscale, hscale)
    # Reset the width/height of the texture in Atlas
    i.w, i.h = pwidth, pheight
text = atlas_cls.atlas.ConvertText # List[str]
sline('1_scale.atlas', text)
```
# Export atlas frames
```python
from pathlib import Path
from PIL.Image import open as imgop
from SpineAtlas import rbin, SpineAtlas, AtlasImg

p = Path.cwd().joinpath('frames')
p.mkdir(parents=True, exist_ok=True)

data = rbin('1.atlas')
atlas_cls = SpineAtlas(data)
texs = {i.png:imgop(i.png) for i in atlas_cls.atlas.atlas} # set png dict
imgs = AtlasImg(texs, atlas_cls) # get frames
for k, v in imgs.items():
    png = p.joinpath(f'{k}.png')
    png.parent.mkdir(parents=True, exist_ok=True)
    v.save(png.as_posix())
```
# Convert other formats to `Spine Atlas`
```python
from SpineAtlas import Atlas, Anchor, AtlasTex, AtlasFrame, ReOffset

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
text = atlas_cls.atlas.ConvertText # List[str]
sline('1.atlas', text)
```
# Recalculate the clipping anchor point
```python
from SpineAtlas import rbin, sline, Anchor, SpineAtlas, ReOffset

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

data = rbin('1.atlas')
atlas_cls = SpineAtlas(data)
# The default anchor point for Spine Atlas clipping is the top left corner
atlas_cls.atlas.cutp = Anchor.BOTTOM_LEFT
ReOffset(atlas_cls.atlas) # Recalculate clipping X/Y starting from the upper left corner
text = atlas_cls.atlas.ConvertText # List[str]
sline('1_ReOffset.atlas', text)
```
# Recalculate the Offset anchor point
```python
from SpineAtlas import rbin, sline, Anchor, SpineAtlas, ReOffset

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

data = rbin('1.atlas')
atlas_cls = SpineAtlas(data)
# The default anchor point for Spine Atlas Offset is the bottom left corner
atlas_cls.atlas.offp = Anchor.TOP_LEFT
ReOffset(atlas_cls.atlas) # Recalculate Offset X/Y starting from the bottom left corner
text = atlas_cls.atlas.ConvertText # List[str]
sline('1_ReOffset.atlas', text)
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
