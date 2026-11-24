# -*- coding: utf-8 -*-
"""
Ajustes para o arquivo de impressao (exigencias da grafica):
  * textos convertidos em curva (os glifos viram desenhos, sem fonte embutida)
  * imagens CMYK gravadas em JPEG de alta qualidade (arquivo < 15 MB)
  * marcacao PDF/X-1a:2001 (OutputIntent, versao 1.3, TrimBox/BleedBox)

Uso: import pdfx; pdfx.ativar()  (antes de desenhar)
     pdfx.finalizar(entrada, saida)  (depois de gerar o PDF)
"""
import io, os
from reportlab.pdfgen import canvas as _cv
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from fontTools.ttLib import TTFont

ASSETS = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets')
FONTES = {'Reg': 'Inter-Regular', 'Med': 'Inter-Medium', 'Semi': 'Inter-SemiBold', 'Bold': 'Inter-Bold',
          'XBold': 'Inter-ExtraBold', 'Disp': 'InterDisplay-Bold', 'Black': 'InterDisplay-Black', 'Ita': 'Inter-Italic'}
_fontes = {}
QUALIDADE_JPEG = 85


def _fonte(nome):
    if nome not in _fontes:
        f = TTFont(os.path.join(ASSETS, 'fonts', FONTES[nome] + '.ttf'))
        _fontes[nome] = (f.getGlyphSet(), f.getBestCmap(), f['head'].unitsPerEm)
    return _fontes[nome]


class _Pen:
    def __init__(self, p, x, y, s):
        self.p, self.x, self.y, self.s = p, x, y, s
    def _t(self, pt): return self.x + pt[0] * self.s, self.y + pt[1] * self.s
    def moveTo(self, pt): self.p.moveTo(*self._t(pt))
    def lineTo(self, pt): self.p.lineTo(*self._t(pt))
    def curveTo(self, *pts):
        a, b, c = [self._t(q) for q in pts]; self.p.curveTo(*a, *b, *c)
    def qCurveTo(self, *pts):
        # converte quadraticas (TrueType) em cubicas
        pts = list(pts)
        if pts[-1] is None: pts = pts[:-1]
        cur = self._cur
        for i in range(len(pts) - 1):
            ctrl = pts[i]
            end = pts[i + 1] if i == len(pts) - 2 else ((pts[i][0] + pts[i + 1][0]) / 2, (pts[i][1] + pts[i + 1][1]) / 2)
            c1 = (cur[0] + 2 / 3 * (ctrl[0] - cur[0]), cur[1] + 2 / 3 * (ctrl[1] - cur[1]))
            c2 = (end[0] + 2 / 3 * (ctrl[0] - end[0]), end[1] + 2 / 3 * (ctrl[1] - end[1]))
            self.p.curveTo(*self._t(c1), *self._t(c2), *self._t(end)); cur = end
        self._cur = cur
    def closePath(self): self.p.close()
    def endPath(self): pass
    def addComponent(self, *a): pass


class _TrackPen(_Pen):
    """Guarda o ponto atual (necessario para as quadraticas)."""
    def moveTo(self, pt): self._cur = pt; super().moveTo(pt)
    def lineTo(self, pt): self._cur = pt; super().lineTo(pt)
    def curveTo(self, *pts): self._cur = pts[-1]; super().curveTo(*pts)


def _texto_curva(self, x, y, txt, *a, **k):
    nome, tam = self._fontname, self._fontsize
    if nome not in FONTES:
        return _orig['drawString'](self, x, y, txt, *a, **k)
    gs, cmap, upm = _fonte(nome)
    s = tam / upm
    p = self.beginPath(); pen = _TrackPen(p, x, y, s)
    cx = 0.0
    from fontTools.pens.recordingPen import DecomposingRecordingPen
    for ch in str(txt):
        g = cmap.get(ord(ch), '.notdef')
        rec = DecomposingRecordingPen(gs); gs[g].draw(rec)
        pen.x = x + cx * s
        for op, args in rec.value:
            getattr(pen, op)(*args)
        cx += gs[g].width
    self.drawPath(p, stroke=0, fill=1)


def _centro(self, x, y, txt, *a, **k):
    w = pdfmetrics.stringWidth(str(txt), self._fontname, self._fontsize)
    _texto_curva(self, x - w / 2, y, txt)


def _direita(self, x, y, txt, *a, **k):
    w = pdfmetrics.stringWidth(str(txt), self._fontname, self._fontsize)
    _texto_curva(self, x - w, y, txt)


def _imagem(self, img, x, y, width=None, height=None, mask=None, **k):
    """Imagens PIL em CMYK vao como JPEG (DCT) para reduzir o tamanho."""
    src = getattr(img, '_image', None) if isinstance(img, ImageReader) else None
    if src is not None and getattr(src, 'mode', '') == 'CMYK':
        b = io.BytesIO(); src.save(b, 'JPEG', quality=QUALIDADE_JPEG, subsampling=0)
        b.seek(0); img = ImageReader(b)
    return _orig['drawImage'](self, img, x, y, width, height, mask=mask, **k)


_orig = {}
def ativar():
    if _orig: return
    for n in ('drawString', 'drawCentredString', 'drawRightString', 'drawImage'):
        _orig[n] = getattr(_cv.Canvas, n)
    _cv.Canvas.drawString = _texto_curva
    _cv.Canvas.drawCentredString = _centro
    _cv.Canvas.drawRightString = _direita
    _cv.Canvas.drawImage = _imagem


def finalizar(entrada, saida, titulo):
    """Adiciona OutputIntent PDF/X-1a e metadados."""
    from pypdf import PdfReader, PdfWriter
    from pypdf.generic import (NameObject, TextStringObject, DictionaryObject, ArrayObject)
    r = PdfReader(entrada); w = PdfWriter()
    for pg in r.pages:
        res = pg['/Resources']
        if '/Font' in res:
            import re
            from pypdf.generic import StreamObject
            dados = pg.get_contents().get_data()
            dados = re.sub(rb'BT\s+/F\d+\s+[\d.]+\s+Tf\s+[\d.]+\s+TL\s+ET', b'', dados)   # bloco vazio do ReportLab
            if b'Tj' not in dados and b'TJ' not in dados and b' Tf' not in dados:
                so = StreamObject(); so.set_data(dados)
                pg[NameObject('/Contents')] = so
                del res[NameObject('/Font')]   # sem texto vivo: remove a Helvetica declarada pelo ReportLab
        w.add_page(pg)
    oi = DictionaryObject({
        NameObject('/Type'): NameObject('/OutputIntent'),
        NameObject('/S'): NameObject('/GTS_PDFX'),
        NameObject('/OutputConditionIdentifier'): TextStringObject('FOGRA39'),
        NameObject('/OutputCondition'): TextStringObject('Coated FOGRA39 (ISO 12647-2:2004)'),
        NameObject('/RegistryName'): TextStringObject('http://www.color.org'),
        NameObject('/Info'): TextStringObject('Coated FOGRA39'),
    })
    w._root_object[NameObject('/OutputIntents')] = ArrayObject([w._add_object(oi)])
    w.add_metadata({'/Title': titulo, '/Creator': 'gerador calendario', '/GTS_PDFXVersion': 'PDF/X-1:2001',
                    '/GTS_PDFXConformance': 'PDF/X-1a:2001'})
    w._info.get_object()[NameObject('/Trapped')] = NameObject('/False')
    w.pdf_header = '%PDF-1.3'
    w.compress_identical_objects()
    with open(saida, 'wb') as f: w.write(f)
