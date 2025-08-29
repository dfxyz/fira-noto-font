#!/usr/bin/env python

from __future__ import annotations
import os
from fontTools.ttLib import TTFont
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.pens.transformPen import TransformPen
from fontTools.misc.transform import Transform
from fontTools.varLib import instancer

os.chdir(os.path.dirname(__file__))

targetFontName = "Fira Noto SC"
targetFontFileName = "FiraNotoSC"
versionString = "0.1.0"
versionFloat = 0.1

# 打开字体文件
if os.path.exists("source/NotoSansSC-Retina.ttf"):
    notoRetinaFont = TTFont("source/NotoSansSC-Retina.ttf")
else:
    if notoVFFont is None:
        notoVFFont = TTFont("source/NotoSansSC-VF.ttf")
    notoRetinaFont = instancer.instantiateVariableFont(notoVFFont, {"wght": 450})
if os.path.exists("source/NotoSansSC-Bold.ttf"):
    notoBoldFont = TTFont("source/NotoSansSC-Bold.ttf")
else:
    if notoVFFont is None:
        notoVFFont = TTFont("source/NotoSansSC-VF.ttf")
    notoBoldFont = instancer.instantiateVariableFont(notoVFFont, {"wght": 700})
firaRetinaFont = TTFont("source/FiraCodeNerdFontPropo-Retina.ttf")
firaBoldFont = TTFont("source/FiraCodeNerdFontPropo-Bold.ttf")


# 修改字体元数据
def modifyMetadata(
    firaFont: TTFont,
    notoFont: TTFont,
    subFamilyName: str,
    overrideWeight: Optional[int] = None,
):
    del firaFont["PfEd"]  # 移除FontLog信息

    firaFont["head"].fontRevision = versionFloat

    def getNameAsStr(nameTable, nameID: int) -> str:
        return nameTable.getName(nameID, 3, 1).toUnicode()

    firaFontName = firaFont["name"]
    notoFontName = notoFont["name"]
    newNameTable = {}
    # 版权信息
    newNameTable[0] = (
        f"{getNameAsStr(firaFontName, 0)}\n{getNameAsStr(notoFontName, 0)}"
    )
    # 字体族名
    newNameTable[1] = targetFontName
    # 样式名
    newNameTable[2] = subFamilyName
    # 唯一标识
    newNameTable[3] = f"{targetFontName} {subFamilyName} {versionString}"
    # 完整字体名，一般是字体族名+样式名
    newNameTable[4] = f"{targetFontName} {subFamilyName}"
    # 版本信息
    newNameTable[5] = (
        f"FiraNotoSC({versionString});FiraNerdFont({getNameAsStr(firaFontName, 5)});NotoSansSC({getNameAsStr(notoFontName, 5)})"
    )
    # PostScript唯一名称（不能包含空格）
    newNameTable[6] = targetFontFileName
    # 商标信息
    newNameTable[7] = (
        f"{getNameAsStr(firaFontName, 7)}\n{getNameAsStr(notoFontName, 7)}"
    )
    # 制造商信息
    newNameTable[8] = (
        f"{getNameAsStr(firaFontName, 8)}\n{getNameAsStr(notoFontName, 8)}"
    )
    # 设计者信息
    newNameTable[9] = (
        f"{getNameAsStr(firaFontName, 9)}\n{getNameAsStr(notoFontName, 9)}"
    )
    # 厂商网站
    newNameTable[11] = (
        f"{getNameAsStr(firaFontName, 11)}\n{getNameAsStr(notoFontName, 11)}"
    )
    # 许可证信息
    newNameTable[13] = getNameAsStr(firaFontName, 13)
    # 许可证URL
    newNameTable[14] = getNameAsStr(firaFontName, 14)
    # 首选字体族名
    newNameTable[16] = targetFontName
    # 首选样式名
    newNameTable[17] = subFamilyName

    def setName(nameID: int, name: str):
        firaFont["name"].setName(name, nameID, 3, 1, 0x409)

    firaFont["name"].names = []
    for nameID, name in newNameTable.items():
        setName(nameID, name)

    # 修改OS/2表
    firaOS2 = firaFont["OS/2"]
    notoOS2 = notoFont["OS/2"]
    if overrideWeight is not None:
        firaOS2.usWeightClass = overrideWeight
    firaOS2.ulUnicodeRange1 |= notoOS2.ulUnicodeRange1
    firaOS2.ulUnicodeRange2 |= notoOS2.ulUnicodeRange2
    firaOS2.ulUnicodeRange3 |= notoOS2.ulUnicodeRange3
    firaOS2.ulUnicodeRange4 |= notoOS2.ulUnicodeRange4
    firaOS2.ulCodePageRange1 |= notoOS2.ulCodePageRange1
    firaOS2.ulCodePageRange2 |= notoOS2.ulCodePageRange2


modifyMetadata(firaRetinaFont, notoRetinaFont, "Regular", 400)  # 使用Retina作为Regular
modifyMetadata(firaBoldFont, notoBoldFont, "Bold")


def mergeFont(firaFont: TTFont, notoFont: TTFont, outputPath: str):
    scale = firaFont["head"].unitsPerEm / notoFont["head"].unitsPerEm
    transform = Transform(scale, 0, 0, scale, 0, 0)

    firaBestCmap: dict[int, str] = firaFont.getBestCmap()
    firaGlyphSet = firaFont.getGlyphSet()
    notoBestCmap: dict[int, str] = notoFont.getBestCmap()
    notoGlyphSet = notoFont.getGlyphSet()

    for code, glyphName in notoBestCmap.items():
        if code in firaBestCmap:
            continue

        # 缩放字形并添加相关数据到firaFont中
        glyph = notoGlyphSet[glyphName]
        pen = TTGlyphPen(notoGlyphSet)
        tpen = TransformPen(pen, transform)
        glyph.draw(tpen)
        scaledGlyph = pen.glyph()
        scaledWidth, scaledLsb = (round(x * scale) for x in notoFont["hmtx"][glyphName])
        if glyphName in firaGlyphSet:
            glyphName = f"noto.{glyphName}"
        firaFont["glyf"][glyphName] = scaledGlyph
        firaFont["hmtx"][glyphName] = (scaledWidth, scaledLsb)
        for table in firaFont["cmap"].tables:
            if not table.isUnicode():
                continue
            if table.format == 4 and code > 0xFFFF:
                continue
            table.cmap[code] = glyphName

    firaFont.save(outputPath)


mergeFont(firaRetinaFont, notoRetinaFont, "target/FiraNotoSC-Regular.ttf")
mergeFont(firaBoldFont, notoBoldFont, "target/FiraNotoSC-Bold.ttf")
