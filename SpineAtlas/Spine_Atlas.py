from math import ceil
from enum import IntEnum
from pathlib import Path
from itertools import cycle
from json import dumps as djson
from attrs import define, field, Factory
from typing import Union, List, Tuple, Type, Dict, Callable, Literal
from numpy import array as nparr, clip as npcp, dstack as npdst, uint8
from PIL.Image import Image, AFFINE, BICUBIC, fromarray as imgarr, new as imgcr, open as imgop

def ctext(data: bytes, encoding: str = '') -> str:
    if encoding:
        try:
            return data.decode(encoding)
        except:
            pass
    try:
        return data.decode('utf-8')
    except:
        return data.decode('utf-8-sig')

def rbin(fp: Union[str, Path], number:int = 0) -> bytes:
    with open(fp, 'rb') as f:
        return f.read() if number == 0 else f.read(number)

def sline(fp: Union[str, Path], data: List[str], encoding: str = 'utf-8') -> None:
    with open(fp, 'w', encoding=encoding) as f:
        f.write('\n'.join(data))

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

@define(slots=True)
class AtlasFrame:
    name: str = ''
    cutx: Union[int, float, str] = 0
    cuty: Union[int, float, str] = 0
    cutw: Union[int, float, str] = 0
    cuth: Union[int, float, str] = 0
    offx: Union[int, float, str] = 0
    offy: Union[int, float, str] = 0
    offw: Union[int, float, str] = 0
    offh: Union[int, float, str] = 0
    rota: int = 0
    arrs: Tuple[str, ...] = ('cutx', 'cuty', 'cutw', 'cuth', 'offx', 'offy', 'offw', 'offh')
    valt: Union[Type[int], Type[float]] = int

    def __attrs_post_init__(self):
        t = self.valt
        for i in self.arrs:
            v = getattr(self, i)
            if isinstance(v, t): continue
            setattr(self, i, t(v))
        if self.offw == 0:
            self.offw = self.cutw
        if self.offh == 0:
            self.offh = self.cuth
        if isinstance(self.rota, str):
            self.rota = 0 if self.rota == 'false' else 90 if self.rota == 'true' else int(self.rota)
        elif isinstance(self.rota, float):
            self.rota = int(self.rota)

@define(slots=True)
class AtlasTex:
    png: str = ''
    w: Union[int, str] = 0
    h: Union[int, str] = 0
    pma: Union[bool, str] = False
    scale: float = 1.0
    frames: List[AtlasFrame] = field(default=Factory(list))
    tex: Image = None

    def __attrs_post_init__(self):
        if isinstance(self.w, str):
            self.w = int(self.w)
        if isinstance(self.h, str):
            self.h = int(self.h)
        if isinstance(self.pma, str):
            self.pma = self.pma == 'true'

@define(slots=True)
class Atlas:
    atlas: List[AtlasTex] = field(default=Factory(list))
    cutp: Anchor = Anchor.TOP_LEFT
    offp: Anchor = Anchor.BOTTOM_LEFT
    version: bool = False # True Atlas-4.0 / False - Atlas-3.8
    covt: Union[Type[int], Callable[[float], int]] = int
    path: Path = None
    name: str = ''

    def SaveAtlas(self, path: Union[Path, str] = None, encoding: str = 'utf-8'):
        old = self.covt
        self.covt = int
        if path is None and self.path is None:
            p = Path().cwd()
        else:
            p = (Path(path) if isinstance(path, str) else path) if path is not None else self.path
        if path is None:
            p.mkdir(parents=True, exist_ok=True)
        else:
            p.parent.mkdir(parents=True, exist_ok=True)
        if path is None: p = p.joinpath(f'{self.name}.atlas')
        atlas = self.ConvertText
        sline(p, atlas, encoding)
        self.covt = old

    def SaveFrames(self, path: Union[Path, str] = None, texpath: Union[Path, str] = None, mode: Literal['Normal', 'Premul', 'NonPremul'] = 'Normal'):
        if path is None and self.path is None:
            p = Path().cwd().joinpath(self.name)
        else:
            p = (Path(path) if isinstance(path, str) else path) if path is not None else self.path.joinpath(self.name)
        if texpath is None and self.path is None:
            p2 = Path().cwd()
        else:
            p2 = (Path(texpath) if isinstance(texpath, str) else texpath) if texpath is not None else self.path
        imgs = self.Frames(p2, mode)
        for k, v in imgs.items():
            w = p.joinpath(k)
            w.parent.mkdir(parents=True, exist_ok=True)
            v.save(f'{w.as_posix()}.png', format='PNG')

    def Frames(self, path: Union[Path, str] = None, mode: Literal['Normal', 'Premul', 'NonPremul'] = 'Normal') -> Dict[str, Image]:
        if path is None and self.path is None:
            p = Path().cwd()
        else:
            p = (Path(path) if isinstance(path, str) else path) if path is not None else self.path
        imgs:Dict[str, Image] = {}
        for i in self.atlas:
            if i.tex is not None:
                tex = i.tex
            else:
                p2 = p.joinpath(i.png)
                if not p2.is_file():
                    print(f'Miss Tex - {p2}')
                    continue
                tex = imgop(p2.as_posix())
            if mode == 'Premul':
                img = ImgPremultiplied(tex)
            elif mode == 'NonPremul':
                img = ImgNonPremultiplied(tex)
            else:
                img = tex
            for j in i.frames:
                imgs[j.name] = CutFrame(img, j)
        return imgs

    def ReScale(self, path: Union[Path, str] = None):
        if path is None and self.path is None:
            p = Path().cwd()
        else:
            p = (Path(path) if isinstance(path, str) else path) if path is not None else self.path
        for i in self.atlas:
            if i.tex is not None:
                tex = i.tex
                w, h = tex.size
            else:
                t = p.joinpath(i.png)
                if not t.is_file():
                    print(f'Miss Tex - {t}')
                    continue
                if rbin(t, 4) == b'\x89PNG':
                    tex = rbin(t, 24)[16:]
                    w, h = int.from_bytes(tex[:4], byteorder='big'), int.from_bytes(tex[4:], byteorder='big')
                else:
                    tex = imgop(t.as_posix())
                    w, h = tex.size
            wscale, hscale = w / i.w, h / i.h
            AtlasScale(i, wscale, hscale, self.covt)
            i.w, i.h = w, h

    def ReOffset(self):
        checka, checkb = self.atlas.cutp != Anchor.TOP_LEFT, self.atlas.offp != Anchor.BOTTOM_LEFT
        indexa, indexb = self.atlas.cutp.value, self.atlas.offp.value
        if not checka and not checkb: return
        for i in self.atlas.atlas:
            for j in i.frames:
                if checka:
                    if indexa == 2:
                        j.cutx = ((i.w - j.cutw) / 2) + j.cutx
                    elif indexa == 3:
                        j.cutx = i.w - (j.cutw + j.cutx)
                    elif indexa == 4:
                        j.cuty = ((i.h - j.cuth) / 2) + j.cuty
                    elif indexa == 5:
                        j.cutx = ((i.w - j.cutw) / 2) + j.cutx
                        j.cuty = ((i.h - j.cuth) / 2) + j.cuty
                    elif indexa == 6:
                        j.cutx = i.w - (j.cutw + j.cutx)
                        j.cuty = ((i.h - j.cuth) / 2) + j.cuty
                    elif indexa == 7:
                        j.cuty = i.h - (j.cuth + j.cuty)
                    elif indexa == 8:
                        j.cutx = ((i.w - j.cutw) / 2) + j.cutx
                        j.cuty = i.h - (j.cuth + j.cuty)
                    elif indexa == 9:
                        j.cutx = i.w - (j.cutw + j.cutx)
                        j.cuty = i.h - (j.cuth + j.cuty)
                if checkb:
                    if indexb == 1:
                        j.offy = j.offh - (j.cuth + j.offy)
                    elif indexb == 2:
                        j.offx = ((j.offw - j.cutw) / 2) + j.offx
                        j.offy = j.offh - (j.cuth + j.offy)
                    elif indexb == 3:
                        j.offx = j.offw - (j.cutw + j.offx)
                        j.offy = j.offh - (j.cuth + j.offy)
                    elif indexb == 4:
                        j.offy = ((j.offh - j.cuth) / 2) + j.offy
                    elif indexb == 5:
                        j.offx = ((j.offw - j.cutw) / 2) + j.offx
                        j.offy = ((j.offh - j.cuth) / 2) + j.offy
                    elif indexb == 6:
                        j.offx = j.offw - (j.cutw + j.offx)
                        j.offy = ((j.offh - j.cuth) / 2) + j.offy
                    elif indexb == 8:
                        j.offx = ((j.offw - j.cutw) / 2) + j.offx
                        j.offy = j.offh - (j.cuth + j.offy)
                    elif indexb == 9:
                        j.offx = j.offw - (j.cutw + j.offx)
                        j.offy = j.offh - (j.cuth + j.offy)
        self.atlas.cutp = Anchor.TOP_LEFT
        self.atlas.offp = Anchor.BOTTOM_LEFT

    @property
    def ConvertText(self) -> List[str]:
        atlas = []
        if self.version:
            for i in self.atlas:
                atlas.extend([i.png, f'size:{self.covt(i.w)},{self.covt(i.h)}', 'filter:Linear,Linear'])
                if i.pma: atlas.append('pma:true')
                if i.scale != 1.0: atlas.append(f'scale:{i.scale}')
                for j in i.frames:
                    cutd = self.covt(j.cutx), self.covt(j.cuty), self.covt(j.cutw), self.covt(j.cuth)
                    atlas.extend([j.name, f'bounds:{cutd[0]},{cutd[1]},{cutd[2]},{cutd[3]}'])
                    offd = self.covt(j.offx), self.covt(j.offy), self.covt(j.offw), self.covt(j.offh)
                    if offd != (0, 0, cutd[2], cutd[3]):
                        atlas.extend([j.name, f'bounds:{offd[0]},{offd[1]},{offd[2]},{offd[3]}'])
                    if j.rota != 0:
                        atlas.append(f'rotate:{j.rota}')
                atlas.append('')
        else:
            for i in self.atlas:
                atlas.extend(['', i.png, f'size: {self.covt(i.w)},{self.covt(i.h)}', 'format: RGBA8888', 'filter: Linear,Linear', 'repeat: none'])
                for j in i.frames:
                    d = 'false' if j.rota == 0 else 'true' if j.rota == 90 else j.rota, self.covt(j.cutx), self.covt(j.cuty), self.covt(j.cutw), self.covt(j.cuth), self.covt(j.offx), self.covt(j.offy), self.covt(j.offw), self.covt(j.offh)
                    atlas.extend([j.name, f'  rotate: {d[0]}', f'  xy: {d[1]}, {d[2]}', f'  size: {d[3]}, {d[4]}', f'  orig: {d[7]}, {d[8]}', f'  offset: {d[5]}, {d[6]}', '  index: -1'])
            atlas.append('')
        return atlas

class Atlas3:
    Tex = 'size:'
    Frame = 'rotate:'

class Atlas4:
    Tex = 'size:'
    Pma = 'pma:'
    Scale = 'scale:'
    Frame = 'bounds:'
    Offset = 'offsets:'
    Rotate = 'rotate:'

class LineTextReader:
    __slots__ = ('stream', 'length', 'pos')

    def __init__(self, string: Union[str, bytes, bytearray, List[str]], encoding: str = 'utf-8', start: int = 0):
        if isinstance(string, (bytes, bytearray)):
            self.stream = ctext(string, encoding).splitlines()
        elif isinstance(string, str):
            self.stream = string.splitlines()
        else:
            self.stream = string
        self.stream = list(filter(bool, self.stream))
        self.length = len(self.stream)
        self.pos = max(0, min(start, self.length))

    def uread(self, number: int = 1, repa: str = '', repb: str = '', mode: bool = True) -> Union[str, List[str]]:
        end = min(self.pos + number, self.length)
        lines = self.stream[self.pos:end]
        if repa: lines = [line.replace(repa, repb) for line in lines]
        if mode: self.pos = end
        return (lines[0] if number == 1 else lines) if lines else ''

    def read(self, number: int = 1, repa: str = '', repb: str = '') -> Union[str, List[str]]:
        return self.uread(number, repa, repb)

    def peek(self, number: int = 1, repa: str = '', repb: str = '') -> Union[str, List[str]]:
        return self.uread(number, repa, repb, False)

    def __iter__(self):
        while self.pos < self.length:
            yield self.read()

class SpineAtlas:
    __slots__ = ('reader', 'version', 'atlas')
    reader: LineTextReader
    version: bool
    atlas: Atlas

    def __init__(self, string: Union[str, bytes, bytearray, List[str]], verison: bool = None, encoding: str = 'utf-8', path: Path = None, name: str = ''):
        self.reader = LineTextReader(string, encoding)
        self.version = False
        if verison is not None:
            self.version = verison
        elif isinstance(string, (bytes, bytearray)):
            self.version = b'bounds:' in string
        elif isinstance(string, str):
            self.version = 'bounds:' in string
        else:
            self.version = 'bounds:' in djson(string)
        self.parse()
        if path is not None: self.atlas.path = path
        self.atlas.name = name if name else Path(self.atlas.atlas[0].png).stem

    def parse(self):
        (self.atlas4 if self.version else self.atlas3)()

    def atlas3(self):
        atlas: List[AtlasTex] = []
        atlasc: AtlasTex = None
        while self.reader.pos < self.reader.length:
            text = self.reader.read()
            ntext = self.reader.peek(repa=' ').lstrip()
            if ntext.startswith(Atlas3.Tex):
                if atlasc is not None:
                    atlas.append(atlasc)
                atlasc = AtlasTex(text, *ntext.split(':', 1)[1].split(','))
                self.reader.pos += 4
            elif ntext.startswith(Atlas3.Frame):
                self.reader.pos += 1
                fdata = []
                for _ in range(4):
                    fdata.extend(self.reader.read(repa=' ').split(':', 1)[1].split(','))
                frame = AtlasFrame(text, *fdata[:4], *fdata[6:8], *fdata[4:6], ntext.split(':', 1)[1])
                atlasc.frames.append(frame)
            else:
                continue
        atlas.append(atlasc)
        self.atlas = Atlas(atlas)

    def atlas4(self):
        atlas: List[AtlasTex] = []
        atlasc: AtlasTex = None
        while self.reader.pos < self.reader.length:
            text = self.reader.read()
            ntext = self.reader.peek(repa=' ').lstrip()
            if ntext.startswith(Atlas4.Tex):
                if atlasc is not None:
                    atlas.append(atlasc)
                tdata = [False, 1.0]
                self.reader.pos += 1
                while True:
                    t = self.reader.read(repa=' ')
                    if ':' not in t:
                        self.reader.pos -= 1
                        break
                    elif t.startswith(Atlas4.Pma):
                        tdata[0] = True
                    elif t.startswith(Atlas4.Scale):
                        tdata[1] = t.split(':', 1)[1]
                atlasc = AtlasTex(text, *ntext.split(':', 1)[1].split(','), *tdata)
            elif ntext.startswith(Atlas4.Frame):
                self.reader.pos += 1
                fdata = [*ntext.split(':', 1)[1].split(','), 0, 0, 0, 0, 'false']
                while True:
                    t = self.reader.read(repa=' ')
                    if ':' not in t:
                        self.reader.pos -= 1
                        break
                    elif t.startswith(Atlas4.Offset):
                        fdata[4:8] = t.split(':', 1)[1].split(',')
                    elif t.startswith(Atlas4.Rotate):
                        fdata[8] = t.split(':', 1)[1]
                frame = AtlasFrame(text, *fdata)
                atlasc.frames.append(frame)
            else:
                continue
        atlas.append(atlasc)
        self.atlas: Atlas = Atlas(atlas, version=True)

def AtlasScale(atlas: AtlasTex, wscale: float = 1.0, hscale: float = 1.0, covt: Union[Type[int], Type[float]] = int):
    if wscale == 1.0 and hscale == 1.0: return
    wh = (wscale, hscale)
    for i in atlas.frames:
        rt = int(i.rota)
        check = rt != 180 and rt != -180 and rt != 0
        if check:
            i.cutw, i.cuth, i.offx, i.offy, i.offw, i.offh = i.cuth, i.cutw, i.offy, i.offx, i.offh, i.offw
        for j, k in zip(i.arrs, cycle(wh)):
            v = getattr(i, j)
            setattr(i, j, covt(v * k))
        if check:
            i.cutw, i.cuth, i.offx, i.offy, i.offw, i.offh = i.cuth, i.cutw, i.offy, i.offx, i.offh, i.offw
        i.valt = covt
    factor = (wscale, atlas.w) if wscale < hscale else (hscale, atlas.h)
    atlas.scale = round((factor[0] / (factor[0] * factor[1])) * atlas.scale, 2)

def CutFrameFloat(tex: Image, frame: AtlasFrame) -> Image:
    x, y, w, h = frame.offx, frame.offy, frame.offw, frame.offh
    cx, cy, cw, ch = frame.cutx, frame.cuty, frame.cutw, frame.cuth
    if frame.rota != 180 and frame.rota != -180 and frame.rota != 0: cw, ch = ch, cw
    matrix = (1, 0, cx, 0, 1, cy)
    cut = tex.transform((ceil(cw), ceil(ch)), AFFINE, matrix, resample=BICUBIC)
    if frame.rota != 0: cut = cut.rotate(frame.rota * -1, expand=True)
    if frame.rota != 180 and frame.rota != -180 and frame.rota != 0: cw, ch = ch, cw
    matrix = (1, 0, x * -1, 0, 1, (h - y - ch) * -1)
    return cut.transform((ceil(w), ceil(h)), AFFINE, matrix, resample=BICUBIC)

def CutFrameInt(tex: Image, frame: AtlasFrame) -> Image:
    x, y, w, h = frame.offx, frame.offy, frame.offw, frame.offh
    cx, cy, cw, ch = frame.cutx, frame.cuty, frame.cutw, frame.cuth
    cw2, ch2 = (cx + ch, cy + cw) if frame.rota != 180 and frame.rota != -180 and frame.rota != 0 else (cx + cw, cy + ch)
    cut = tex.crop((cx, cy, cw2, ch2))
    if frame.rota != 0: cut = cut.rotate(frame.rota * -1, expand=True)
    img = imgcr('RGBA', (w, h), (0, 0, 0, 0))
    img.paste(cut, (x, (h - y - ch)))
    return img

def CutFrame(tex: Image, frame: AtlasFrame) -> Image:
    return CutFrameInt(tex, frame) if frame.valt == int else CutFrameFloat(tex, frame)

def AtlasImg(tex: Union[Image, Dict[str, Image]], atlas: Union[SpineAtlas, Atlas, AtlasTex, List[AtlasTex], AtlasFrame, List[AtlasFrame]]) -> Dict[str, Image]:
    if isinstance(atlas, SpineAtlas):
        atlas = atlas.atlas.atlas
    elif isinstance(atlas, Atlas):
        atlas = atlas.atlas
    elif isinstance(atlas, AtlasTex):
        atlas = atlas.frames
    elif isinstance(atlas, AtlasFrame):
        return {atlas.name:CutFrame(tex, atlas)}
    imgs = {}
    if isinstance(atlas[0], AtlasTex):
        check = isinstance(tex, dict)
        for i in atlas:
            img = tex[i.png] if check else tex
            for j in i.frames:
                imgs[j.name] = CutFrame(img, j)
    else:
        for i in atlas:
            imgs[i.name] = CutFrame(tex, i)
    return imgs

def ImgPremultiplied(image: Image) -> Image:
    arr = nparr(image)
    r, g, b, a = arr[:, :, 0], arr[:, :, 1], arr[:, :, 2], arr[:, :, 3]
    mark = (a != 0)
    alpha = 255.0 / a[mark]
    r[mark] = npcp((r[mark] * alpha), 0, 255).astype(uint8)
    g[mark] = npcp((g[mark] * alpha), 0, 255).astype(uint8)
    b[mark] = npcp((b[mark] * alpha), 0, 255).astype(uint8)
    tex = npdst((r, g, b, a))
    return imgarr(tex)

def ImgNonPremultiplied(image: Image) -> Image:
    width, height = image.size
    a = image.split()[-1]
    tex = imgcr("RGBA", (width, height), (0, 0, 0, 255))
    tex.paste(im=image, box=(0, 0), mask=a)
    tex.putalpha(a)
    return tex

def ReadAtlas(data: Union[str, bytes, bytearray, List[str]], verison: bool = None, encoding: str = 'utf-8', path: Union[Path, str] = None, name: str = '') -> Atlas:
    p = None if path is None else (Path(path) if isinstance(path, str) else path)
    return SpineAtlas(data, verison, encoding, p).atlas

def ReadAtlasFile(fp: Union[str, Path], verison: bool = None, encoding: str = 'utf-8', path: Union[Path, str] = None, name: str = '') -> Atlas:
    p = (Path(fp) if isinstance(fp, str) else fp).parent if path is None else (Path(path) if isinstance(path, str) else path)
    return SpineAtlas(rbin(fp), verison, encoding, p).atlas
