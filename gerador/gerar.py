# -*- coding: utf-8 -*-
"""
Gera as artes do calendario 2027 (Clinica Veterinaria Fernanda Calixto + VillaPet)
sobre os gabaritos da grafica.

Uso:  python3 gerar.py <pasta_gabaritos> <pasta_saida>

O calendario (datas, feriados, fases da lua) e reaproveitado do proprio gabarito
da grafica: removemos as linhas-guia, recolorimos para as cores das marcas e
montamos a arte em volta.
"""
import os, re, sys, io
from pypdf import PdfReader, PdfWriter, Transformation
from pypdf.generic import RectangleObject, StreamObject, NameObject
from reportlab.pdfgen import canvas
from reportlab.lib.colors import CMYKColor
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.utils import ImageReader

AQUI = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(AQUI, 'assets')

# ---------------------------------------------------------------- fontes
for nome, arq in [('Reg', 'Inter-Regular'), ('Med', 'Inter-Medium'), ('Semi', 'Inter-SemiBold'),
                  ('Bold', 'Inter-Bold'), ('XBold', 'Inter-ExtraBold'), ('Disp', 'InterDisplay-Bold'),
                  ('Black', 'InterDisplay-Black'), ('Ita', 'Inter-Italic')]:
    pdfmetrics.registerFont(TTFont(nome, os.path.join(ASSETS, 'fonts', arq + '.ttf')))

# ---------------------------------------------------------------- cores (CMYK)
ROSA      = CMYKColor(0.10, 0.82, 0.15, 0.00)   # rosa Fernanda Calixto
ROSA_ESC  = CMYKColor(0.35, 0.95, 0.25, 0.20)   # vinho/magenta escuro
ROSA_MED  = CMYKColor(0.02, 0.45, 0.08, 0.00)
ROSA_CLA  = CMYKColor(0.00, 0.18, 0.06, 0.00)
ROSA_BG   = CMYKColor(0.00, 18/255, 5/255, 0.00)
AMARELO   = CMYKColor(0.00, 0.30, 0.95, 0.00)   # amarelo VillaPet
MARROM    = CMYKColor(0.45, 0.55, 0.60, 0.45)   # marrom VillaPet
BRANCO    = CMYKColor(0, 0, 0, 0)

def k(c):  # CMYK -> operador PDF de preenchimento
    return '%.4f %.4f %.4f %.4f k' % (c.cyan, c.magenta, c.yellow, c.black)

# troca de cores do calendario do gabarito
RECOLOR = {
    '0.0000 1.0000 1.0000 0.0000 k': k(ROSA),                          # vermelho -> rosa
    '0.0000 1.0000 1.0000 0.0000 K': k(ROSA).replace(' k', ' K'),
    '0.0902 0.0588 0.0588 0.0000 k': '0.0000 0.0600 0.0250 0.0000 k',   # caixinhas dos dias
    '0.0000 0.0000 0.0000 0.5020 k': k(MARROM),                        # bolinhas dias da semana / lua
    '0.0000 0.0000 0.0000 0.3020 k': '0.2500 0.3200 0.3500 0.1000 k',  # sabado (mais claro)
}

# ---------------------------------------------------------------- textos
FER_TEL = '(16) 99278-4824'
VILLA_TEL = '(16) 99311-4224'
FER_IG = '@fer_calixto_clinica_vet'
VILLA_IG = '@villapet_'
ENDERECO = 'Rua Expedicionário Solano, 510 • Jd. Soljumar • Sertãozinho/SP'

DICAS = [  # uma por mes (calendario wire-o)
    'Calor forte: água fresca sempre e passeios só fora do sol do meio-dia.',
    'Carnaval: barulho e fogos assustam. Deixe seu pet seguro em casa.',
    'Pulgas e carrapatos: mantenha a prevenção em dia o ano todo.',
    'Check-up anual: prevenir é o melhor jeito de cuidar.',
    'Esfriou? Caminha quentinha e banho com secagem completa.',
    'Festa junina: cuidado com fogos e comidas da festa.',
    'Férias? Planeje com antecedência a estadia do seu pet.',
    '08 – Dia Internacional do Gato  •  26 – Dia do Cachorro',
    '09 – Dia do Médico-Veterinário: obrigado por cuidar!',
    '04 – Dia Mundial dos Animais',
    'Escovação dental previne tártaro e mau hálito.',
    'Fim de ano: fogos e ceia pedem cuidado redobrado com seu pet.',
]

# ---------------------------------------------------------------- utilidades de PDF
def calendario_do_gabarito(caminho, pagina, descartar, w, h, remover=()):
    """Devolve a pagina do gabarito em escala 1:1, sem linhas-guia e recolorida."""
    r = PdfReader(caminho)
    pg = r.pages[pagina]
    c = pg.get_contents().get_data().decode('latin1')
    c = re.sub(r'^q 0 0 595 841 re W\* n [\d.]+ 0 0 [\d.]+ [\d.]+ [\d.]+ cm', 'q', c)
    segs = c.split('/GS9 gs')
    segs = [s for i, s in enumerate(segs) if i not in descartar]
    c = '/GS9 gs'.join(segs)
    for a in remover:
        c = re.sub(a, '', c, flags=re.S)
    for a, b in RECOLOR.items():
        c = c.replace(a, b)
    w_ = PdfWriter()
    so = StreamObject(); so._data = c.encode('latin1')
    pg[NameObject('/Contents')] = so
    for b in ['/CropBox', '/BleedBox', '/TrimBox', '/ArtBox']:
        if b in pg: del pg[b]
    pg.mediabox = RectangleObject([0, 0, w, h])
    return pg


def camadas(fundo_pdf, gabarito_pg, frente_pdf, transf=None):
    base = PdfReader(io.BytesIO(fundo_pdf)).pages[0]
    if transf is None:
        base.merge_page(gabarito_pg)
    else:
        base.merge_transformed_page(gabarito_pg, transf)
    base.merge_page(PdfReader(io.BytesIO(frente_pdf)).pages[0])
    return base

# ---------------------------------------------------------------- desenhos
def pata(c, x, y, s, cor, ang=0):
    """Pegada estilizada centrada em (x,y), tamanho s."""
    c.saveState(); c.translate(x, y); c.rotate(ang); c.setFillColor(cor)
    c.ellipse(-0.42*s, -0.40*s, 0.42*s, 0.22*s, stroke=0, fill=1)
    for dx, dy, rx, ry in [(-0.50, 0.35, 0.15, 0.19), (-0.18, 0.58, 0.15, 0.20),
                           (0.18, 0.58, 0.15, 0.20), (0.50, 0.35, 0.15, 0.19)]:
        c.ellipse((dx-rx)*s, (dy-ry)*s, (dx+rx)*s, (dy+ry)*s, stroke=0, fill=1)
    c.restoreState()


def imagem(c, nome, x, y, w=None, h=None):
    ir = ImageReader(os.path.join(ASSETS, nome))
    iw, ih = ir.getSize()
    if w is None: w = h * iw / ih
    if h is None: h = w * ih / iw
    c.drawImage(ir, x, y, w, h, mask='auto')
    return w, h


def cartao_fernanda(c, x, y, w, raio=8):
    ir = ImageReader(os.path.join(ASSETS, 'fernanda_cartao.png'))
    iw, ih = ir.getSize(); h = w * ih / iw
    c.saveState()
    c.setFillColor(CMYKColor(0.3, 0.6, 0.3, 0.3, alpha=0.25))
    c.roundRect(x + 1.2, y - 1.6, w, h, raio, stroke=0, fill=1)        # sombra suave
    c.restoreState()
    c.saveState()
    p = c.beginPath(); p.roundRect(x, y, w, h, raio); c.clipPath(p, stroke=0, fill=0)
    c.drawImage(ir, x, y, w, h)
    c.restoreState()
    c.setStrokeColor(BRANCO); c.setLineWidth(1.6)
    c.roundRect(x, y, w, h, raio, stroke=1, fill=0)
    return h


def _rgb2cmyk(a):
    import numpy as np
    rgb = a[..., :3] / 255.0
    k = 1 - rgb.max(-1)
    d = np.maximum(1 - k, 1e-6)
    cmy = (1 - rgb - k[..., None]) / d[..., None]
    return np.dstack([cmy, k])


_CACHE = {}
def imagem_cmyk(c, nome, x, y, w=None, h=None, fundo=None, disco_branco=None):
    """Imagem achatada (sem transparencia) em CMYK sobre a cor de fundo exata -> compativel PDF/X-1a."""
    import numpy as np
    from PIL import Image
    chave = (nome, str(fundo), disco_branco)
    if chave not in _CACHE:
        im = Image.open(os.path.join(ASSETS, nome)).convert('RGBA')
        a = np.asarray(im).astype(float)
        al = a[..., 3:4] / 255.0
        cmyk = _rgb2cmyk(a)
        f = np.array([fundo.cyan, fundo.magenta, fundo.yellow, fundo.black]) if fundo else np.zeros(4)
        bg = np.broadcast_to(f, cmyk.shape).copy()
        if disco_branco:
            H, W = al.shape[:2]; yy, xx = np.mgrid[0:H, 0:W]
            R = W / 2 * disco_branco
            bg[((xx - W/2 + .5)**2 + (yy - H/2 + .5)**2) <= R*R] = 0
        out = cmyk * al + bg * (1 - al)
        _CACHE[chave] = Image.fromarray((out * 255).round().astype('uint8'), 'CMYK')
    img = _CACHE[chave]
    iw, ih = img.size
    if w is None: w = h * iw / ih
    if h is None: h = w * ih / iw
    c.drawImage(ImageReader(img), x, y, w, h)
    return w, h


def selo_fernanda(c, cx, cy, r, fundo=None):
    if fundo is not None:
        c.setFillColor(BRANCO); c.circle(cx, cy, r + 1.2, stroke=0, fill=1)
        imagem_cmyk(c, 'fernanda_pata.png', cx - r, cy - r, 2*r, 2*r, fundo=fundo, disco_branco=(r + 1.2) / r)
        return

    c.setFillColor(BRANCO); c.circle(cx, cy, r + 1.2, stroke=0, fill=1)
    imagem(c, 'fernanda_pata.png', cx - r, cy - r, 2*r, 2*r)


def texto_centro(c, txt, x, y, fonte, tam, cor):
    c.setFont(fonte, tam); c.setFillColor(cor); c.drawCentredString(x, y, txt)


def ajustar(c, txt, fonte, tam_max, largura):
    t = tam_max
    while pdfmetrics.stringWidth(txt, fonte, t) > largura and t > 3: t -= 0.1
    return t


def barra_ano(c, u0, u1, v0, v1):
    c.setFillColor(ROSA_ESC)
    c.roundRect(u0, v0, u1 - u0, v1 - v0, (v1 - v0) / 2, stroke=0, fill=1)
    texto_centro(c, '2027', (u0 + u1) / 2, v0 + 2.3, 'Black', 7.6, BRANCO)

# =================================================================== MESA 26,8 x 14,65
MW, MH = 771.0236, 428.0315   # documento com sangria (pt)
DOBRA = 385.49                # centro da dobra (x)

def face(c, lado):
    """Sistema local da face: u = horizontal de leitura (0..428), v = vertical (0 = base, ~385 = dobra)."""
    c.saveState()
    if lado == 'frente':      # metade direita do gabarito
        c.transform(0, 1, -1, 0, MW, 0)
    else:                     # metade esquerda
        c.transform(0, -1, 1, 0, 0, MH)


def mesa_fundo(c, lado):
    face(c, lado)
    U, V = MH, MW - DOBRA
    c.setFillColor(BRANCO); c.rect(-5, -5, U + 10, V + 0.3, stroke=0, fill=1)
    # painel de arte (lado esquerdo da face) com degrade rosa, ate a dobra
    p = c.beginPath(); p.rect(-5, -5, 257, V + 5.3)
    c.saveState(); c.clipPath(p, stroke=0, fill=0)
    c.linearGradient(250, V, 0, 110, (CMYKColor(0.00, 0.22, 0.10, 0.00), CMYKColor(0.12, 0.70, 0.15, 0.02)), extend=True)
    c.restoreState()
    # faixa da base (fora da area de seguranca: so decorativa)
    p = c.beginPath(); p.rect(-5, -5, U + 10, 118)
    c.saveState(); c.clipPath(p, stroke=0, fill=0)
    c.linearGradient(0, 0, U, 118, (CMYKColor(0.12, 0.70, 0.15, 0.02), CMYKColor(0.05, 0.50, 0.10, 0.0)), extend=True)
    c.restoreState()
    c.setFillColor(AMARELO); c.rect(-5, 113, U + 10, 3.2, stroke=0, fill=1)
    for i, (x, y, s, a) in enumerate([(40, 60, 22, -20), (110, 30, 16, 15), (190, 75, 20, -10), (270, 35, 18, 20),
                                      (345, 70, 22, -15), (405, 28, 15, 10)]):
        pata(c, x, y, s, CMYKColor(0.0, 0.25, 0.08, 0.0, alpha=0.45), a)
    # pegadas discretas no painel rosa
    for x, y, s, a in [(222, 140, 14, 25), (24, 352, 12, -20)]:
        pata(c, x, y, s, CMYKColor(0.0, 0.30, 0.10, 0.0, alpha=0.6), a)
    c.restoreState()


def mesa_frente(c, lado):
    face(c, lado)
    if lado == 'frente':
        barra_ano(c, 258.5, 411.0, 349.5, 360.5)
        # cartao Fernanda Calixto + logo VillaPet
        h = cartao_fernanda(c, 36, 203, 194, raio=10)
        c.setFillColor(BRANCO)
        c.roundRect(36, 132, 194, 58, 10, stroke=0, fill=1)
        imagem(c, 'villapet.png', 52, 141, w=162)
    else:
        barra_ano(c, 258.5, 411.0, 349.5, 360.5)
    c.restoreState()


def mesa_verso_textos(c):
    """Textos de contato na face de tras (julho-dezembro)."""
    face(c, 'verso')
    x0, x1 = 24, 244
    cx = (x0 + x1) / 2
    texto_centro(c, 'Lado a lado,', cx, 337, 'Black', 19, ROSA_ESC)
    texto_centro(c, 'cuidando de quem você ama.', cx, 322, 'Semi', 10.2, ROSA_ESC)
    # cartao branco com as duas empresas
    c.setFillColor(BRANCO); c.roundRect(x0, 150, x1 - x0, 160, 10, stroke=0, fill=1)
    # Fernanda
    selo_fernanda(c, x0 + 26, 280, 17)
    c.setFillColor(ROSA_ESC); c.setFont('Med', 6.6); c.drawString(x0 + 50, 289, 'Clínica Veterinária')
    c.setFont('Black', 11.5); c.drawString(x0 + 50, 277, 'Fernanda Calixto')
    c.setFillColor(MARROM); c.setFont('Reg', 5.6)
    c.drawString(x0 + 50, 268, 'Consultas • Vacinas • Cirurgias • Internação')
    c.setFont('Bold', 7.4); c.setFillColor(ROSA)
    c.drawString(x0 + 12, 249, 'WhatsApp ' + FER_TEL)
    c.setFont('Med', 6.4); c.setFillColor(MARROM)
    c.drawRightString(x1 - 12, 249.3, FER_IG)
    c.setStrokeColor(ROSA_CLA); c.setLineWidth(0.8); c.line(x0 + 12, 238, x1 - 12, 238)
    # VillaPet
    imagem(c, 'villapet.png', x0 + 12, 202, w=100)
    c.setFillColor(MARROM); c.setFont('Semi', 6.6)
    c.drawRightString(x1 - 12, 220, 'Pet Shop')
    c.drawRightString(x1 - 12, 211, 'Banho e Tosa')
    c.setFont('Bold', 7.4); c.setFillColor(ROSA)
    c.drawString(x0 + 12, 183, 'WhatsApp ' + VILLA_TEL)
    c.setFont('Med', 6.4); c.setFillColor(MARROM)
    c.drawRightString(x1 - 12, 183.3, VILLA_IG)
    # endereco
    c.setFillColor(ROSA_BG); c.roundRect(x0 + 8, 157, x1 - x0 - 16, 16, 8, stroke=0, fill=1)
    t = ajustar(c, ENDERECO, 'Semi', 6.2, x1 - x0 - 26)
    texto_centro(c, ENDERECO, cx, 162.6, 'Semi', t, ROSA_ESC)
    texto_centro(c, 'Saúde e cuidado no mesmo endereço', cx, 133, 'Bold', 7.6, BRANCO)
    c.restoreState()


def gerar_mesa(gabarito, saida):
    buf_f = io.BytesIO(); c = canvas.Canvas(buf_f, pagesize=(MW, MH))
    mesa_fundo(c, 'frente'); mesa_fundo(c, 'verso')
    # fundo branco na faixa da dobra e no restante
    c.save()
    buf_t = io.BytesIO(); c = canvas.Canvas(buf_t, pagesize=(MW, MH))
    mesa_frente(c, 'frente'); mesa_frente(c, 'verso'); mesa_verso_textos(c)
    c.save()
    cal = calendario_do_gabarito(gabarito, 0, {2, 3, 4, 5, 14}, MW, MH,
                                 remover=[r'/Im11 Do', r'/Im20 Do'])
    pg = camadas(buf_f.getvalue(), cal, buf_t.getvalue())
    w = PdfWriter(); w.add_page(pg)
    w.add_metadata({'/Title': 'Calendário de Mesa 2027 - Fernanda Calixto + VillaPet'})
    w.write(saida)

# =================================================================== WIRE-O 8,8 x 8,8
WW = 261.5748
ESCALA = 0.80
TOPO = 225.0            # ponto fixo (topo do calendario) para a reducao


def wire_fundo(c, mes):
    c.setFillColor(BRANCO); c.rect(0, 0, WW, WW, stroke=0, fill=1)
    # rodape com as marcas
    c.setFillColor(ROSA_BG); c.rect(0, 0, WW, 57, stroke=0, fill=1)
    c.setFillColor(ROSA); c.rect(0, 46, WW, 11, stroke=0, fill=1)


def wire_frente(c, mes):
    # dica do mes
    dica = DICAS[mes]
    t = ajustar(c, dica, 'Semi', 6.0, 220)
    c.setFillColor(BRANCO); c.setFont('Semi', t)
    pata(c, 22, 51.5, 6, AMARELO)
    c.drawString(29, 49.4, dica)
    # Fernanda
    selo_fernanda(c, 31, 27, 13, fundo=ROSA_BG)
    c.setFillColor(ROSA_ESC); c.setFont('Med', 4.6); c.drawString(48, 33.5, 'Clínica Veterinária')
    c.setFont('Black', 7.6); c.drawString(48, 25.6, 'Fernanda Calixto')
    c.setFillColor(MARROM); c.setFont('Semi', 5.2); c.drawString(48, 18.2, FER_TEL)
    # divisor
    c.setStrokeColor(ROSA_CLA); c.setLineWidth(0.7); c.line(134, 15, 134, 39)
    # VillaPet
    imagem_cmyk(c, 'villapet.png', 153, 20.5, w=72, fundo=ROSA_BG)
    c.setFillColor(MARROM); c.setFont('Semi', 5.2)
    c.drawCentredString(189, 12.6, VILLA_TEL)


def gerar_wire(gabarito, saida):
    w = PdfWriter()
    for mes in range(12):
        bf = io.BytesIO(); c = canvas.Canvas(bf, pagesize=(WW, WW)); wire_fundo(c, mes); c.save()
        bt = io.BytesIO(); c = canvas.Canvas(bt, pagesize=(WW, WW)); wire_frente(c, mes); c.save()
        cal = calendario_do_gabarito(gabarito, mes, {1, 2, 3}, WW, WW)
        cx = WW / 2
        tr = Transformation().translate(-cx, -TOPO).scale(ESCALA, ESCALA).translate(cx, TOPO)
        pg = camadas(bf.getvalue(), cal, bt.getvalue(), tr)
        pg.trimbox = RectangleObject([6.063, 6.063, 255.512, 255.512])   # corte final 8,8 x 8,8 cm
        pg.bleedbox = RectangleObject([0, 0, WW, WW])                    # sangria 2 mm
        w.add_page(pg)
    w.add_metadata({'/Title': 'Calendário Wire-o 2027 - Fernanda Calixto + VillaPet'})
    w.write(saida)


if __name__ == '__main__':
    gab, out = sys.argv[1], sys.argv[2]
    os.makedirs(out, exist_ok=True)
    gerar_mesa(os.path.join(gab, 'Calendario_de_Mesa_26.80x14.65_-_4x0.pdf'),
               os.path.join(out, 'Calendario_Mesa_26.80x14.65_FernandaCalixto_VillaPet.pdf'))
    gerar_wire(os.path.join(gab, 'Calendario_Mesa_Wire-o_8.80x8.80_-_4x4.pdf'),
               os.path.join(out, 'Calendario_Wire-o_8.80x8.80_FernandaCalixto_VillaPet.pdf'))
    print('ok')
