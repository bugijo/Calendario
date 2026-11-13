# -*- coding: utf-8 -*-
"""
5 modelos de calendario wire-o 2027 (8,8 x 8,8 cm) - Fernanda Calixto + VillaPet

  1 Foto do Mes      - foto grande no topo, calendario embaixo
  2 Lado a Lado      - cabecalho dividido clinica (rosa) | pet shop (amarelo), foto redonda no centro
  3 Polaroid         - fundo rosado, foto estilo polaroid inclinada
  4 Minimalista      - branco, tipografia fina, numero do mes gigante, foto redonda
  5 Ilustrado        - versao com desenhos (sem fotos)

Fotos: dominio publico (CC0) - ver assets/fotos/CREDITOS_E_LICENCAS.tsv
Tudo em CMYK e sem transparencia.

Uso: python3 modelos.py <pasta_saida>
"""
import os, sys, calendar
import numpy as np
from PIL import Image
from reportlab.pdfgen import canvas
from reportlab.lib.colors import CMYKColor
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from pypdf import PdfReader, PdfWriter
from pypdf.generic import RectangleObject

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gerar as G
import wireo_v2 as V

ROSA, ROSA_ESC, ROSA_CLA, ROSA_BG = G.ROSA, G.ROSA_ESC, G.ROSA_CLA, G.ROSA_BG
AMARELO, MARROM, BRANCO = G.AMARELO, G.MARROM, G.BRANCO
AMARELO_BG = CMYKColor(0.0, 18/255, 70/255, 0.0)       # amarelinho claro (mesmos valores na imagem e no vetor)
AMARELO_ESC = CMYKColor(0.0, 0.45, 0.95, 0.10)
CINZA = CMYKColor(0.30, 0.40, 0.40, 0.25)
PW, B, T = V.PW, V.B, V.T
FOTOS = os.path.join(G.ASSETS, 'fotos')

# foto por mes: (arquivo, foco x, foco y)
FOTO_MES = [('cbb53da2', .5, .38), ('e4c43097', .5, .38), ('1cdf7866', .5, .45), ('2d6367d0', .5, .38),
            ('59c47045', .45, .55), ('e58e8c52', .45, .45), ('6d31a835', .5, .5), ('3a2c86a7', .5, .45),
            ('157e6ada', .58, .38), ('2b3f99ba', .55, .38), ('e30322dc', .5, .45), ('14bb3dc7', .62, .45)]
LEGENDA_FOTO = ['Verão com saúde', 'Carinho todo dia', 'Amor em dobro', 'Juntinhos e cuidados',
                'Quentinho e protegido', 'Hora de brincar!', 'Férias com seu pet', 'Mês dos pets!',
                'Cuidado de verdade', 'Banho & tosa', 'Sorria!', 'Boas festas!']


# ------------------------------------------------------------------ fotos (CMYK, sem transparencia)
def _cmyk(a):
    rgb = a / 255.0
    cmy = 1 - rgb
    k = cmy.min(-1) * 0.75                      # GCR parcial
    d = np.maximum(1 - k, 1e-6)
    c = (cmy - k[..., None]) / d[..., None]
    return np.dstack([c, k])

_cache = {}
def foto(c, mes, x, y, w, h, forma='ret', raio=0, dpi=300):
    nome, fx, fy = FOTO_MES[mes]
    chave = (nome, round(w / h, 3))
    if chave not in _cache:
        im = Image.open(os.path.join(FOTOS, nome + '.jpg')).convert('RGB')
        iw, ih = im.size; alvo = w / h
        if iw / ih > alvo:
            cw, ch = ih * alvo, ih
        else:
            cw, ch = iw, iw / alvo
        x0 = min(max(fx * iw - cw / 2, 0), iw - cw); y0 = min(max(fy * ih - ch / 2, 0), ih - ch)
        im = im.crop((int(x0), int(y0), int(x0 + cw), int(y0 + ch)))
        px = int(w / 72 * dpi)
        if im.size[0] < px: im = im.resize((px, int(px / alvo)), Image.LANCZOS)
        a = _cmyk(np.asarray(im).astype(float))
        _cache[chave] = Image.fromarray((a * 255).round().astype('uint8'), 'CMYK')
    c.saveState()
    p = c.beginPath()
    if forma == 'circ': p.circle(x + w / 2, y + h / 2, w / 2)
    elif raio: p.roundRect(x, y, w, h, raio)
    else: p.rect(x, y, w, h)
    c.clipPath(p, stroke=0, fill=0)
    c.drawImage(ImageReader(_cache[chave]), x, y, w, h)
    c.restoreState()


# ------------------------------------------------------------------ calendario generico
def grade(c, m, x0, x1, y0, y1, est):
    """Desenha dias da semana + dias. est = dict de estilo."""
    cols = 7; cw = (x1 - x0) / cols
    wh = est.get('sem_h', 8.0)
    # dias da semana
    for i, l in enumerate('DSTQQSS'):
        cx = x0 + cw * (i + .5)
        if est.get('sem_pill'):
            c.setFillColor(est['sem_dom_bg'] if i == 0 else est['sem_bg'])
            c.roundRect(cx - cw / 2 + 1, y1 - wh, cw - 2, wh, wh / 2, stroke=0, fill=1)
        c.setFillColor(est['sem_dom_txt'] if i == 0 else est['sem_txt'])
        c.setFont(est.get('sem_fonte', 'Black'), est.get('sem_tam', 5.4))
        c.drawCentredString(cx, y1 - wh + (wh - est.get('sem_tam', 5.4) * .72) / 2, l)
    sem = calendar.Calendar(firstweekday=6).monthdayscalendar(2027, m)
    n = len(sem)
    gy1 = y1 - wh - est.get('gap', 1.5)
    rh = (gy1 - y0) / n
    fases = dict(V.LUAS[m])
    for li, semana in enumerate(sem):
        for ci, d in enumerate(semana):
            if not d: continue
            x = x0 + cw * ci; y = gy1 - rh * (li + 1)
            fer = (m, d) in V.FERIADOS; pet = (m, d) in V.PET
            estilo = est['celula']
            if fer: fundo, txt = est['fer_bg'], est['fer_txt']
            elif pet: fundo, txt = est['pet_bg'], est['pet_txt']
            else: fundo, txt = est['cel_bg'], (est['dom_txt'] if ci == 0 else est['txt'])
            cx, cy = x + cw / 2, y + rh / 2
            if fundo is not None:
                c.setFillColor(fundo)
                if estilo == 'circ':
                    r = min(cw, rh) / 2 - .6
                    c.circle(cx, cy, r, stroke=0, fill=1)
                else:
                    c.roundRect(x + .8, y + .7, cw - 1.6, rh - 1.4, est.get('raio', 2.5), stroke=0, fill=1)
            fs = min(est.get('tam_max', 11), rh * est.get('tam_rel', .6))
            f = est['fonte_dest'] if (fer or pet or ci == 0) else est['fonte']
            c.setFillColor(txt); c.setFont(f, fs)
            dx = -1.2 if (d in fases and est.get('lua') == 'canto') else 0
            c.drawCentredString(cx + dx, cy - fs * .36, str(d))
            if d in fases and est.get('lua'):
                cor = txt if (fer or pet) else est.get('lua_cor', MARROM)
                bg = fundo if fundo is not None else BRANCO
                if est['lua'] == 'canto':
                    V.lua(c, x + cw - 3.6, y + rh - 3.3, 1.45, fases[d], cor, bg)
                elif est['lua'] == 'lado':
                    off = (min(cw, rh) / 2 + .9) if (fer or pet) and estilo == 'circ' else pdfmetrics.stringWidth(str(d), f, fs) / 2 + 2.6
                    V.lua(c, cx + off, cy + fs * .28, 1.25, fases[d], est.get('lua_cor', MARROM) if (fer or pet) else cor, BRANCO)
                else:   # embaixo do numero
                    V.lua(c, cx, y + 2.0, 1.2, fases[d], cor, bg)
            if pet and est.get('pata_pet', True):
                G.pata(c, x + 3.6, y + rh - 3.6, 2.6, est.get('pata_cor', BRANCO), -15)


def legenda(c, m, x0, x1, y, tam=4.8, cor_num=ROSA, cor_txt=CINZA, cor_pet=AMARELO_ESC, fonte='Semi'):
    por_dia = {}
    for fonte_d in (V.FERIADOS, V.PET, V.COMEMORATIVAS):
        for (mm, d), t in fonte_d.items():
            if mm == m: por_dia.setdefault(d, []).append(t)
    partes = [('%02d' % d, ' / '.join(por_dia[d]), (m, d) in V.PET and (m, d) not in V.FERIADOS) for d in sorted(por_dia)]
    if not partes: return
    texto = '   '.join(a + ' ' + b for a, b, _ in partes)
    fs = G.ajustar(c, texto, fonte, tam, x1 - x0)
    x = x0
    for num, txt, ehpet in partes:
        c.setFillColor(cor_pet if ehpet else cor_num); c.setFont('Black', fs); c.drawString(x, y, num)
        x += pdfmetrics.stringWidth(num + ' ', 'Black', fs)
        c.setFillColor(cor_txt); c.setFont(fonte, fs); c.drawString(x, y, txt)
        x += pdfmetrics.stringWidth(txt + '   ', fonte, fs)


def marcas(c, y, fundo, x0=14, x1=248, escala=1.0, tel=True, divisor=True):
    """Bloco com as duas marcas lado a lado. y = base."""
    s = escala
    G.selo_fernanda(c, x0 + 12 * s, y + 13 * s, 11 * s, fundo=fundo)
    tx = x0 + 27 * s
    c.setFillColor(ROSA_ESC); c.setFont('Med', 4.2 * s); c.drawString(tx, y + 18.5 * s, 'Clínica Veterinária')
    c.setFont('Black', 7.0 * s); c.drawString(tx, y + 11.2 * s, 'Fernanda Calixto')
    if tel:
        c.setFillColor(MARROM); c.setFont('Semi', 4.9 * s); c.drawString(tx, y + 4.4 * s, G.FER_TEL)
    meio = (x0 + x1) / 2 + 4
    if divisor:
        c.setStrokeColor(ROSA_CLA); c.setLineWidth(.6); c.line(meio, y + 2 * s, meio, y + 24 * s)
    lw = 66 * s
    lx = (meio + x1) / 2 - lw / 2
    G.imagem_cmyk(c, 'villapet.png', lx, y + 8.5 * s, w=lw, fundo=fundo)
    if tel:
        c.setFillColor(MARROM); c.setFont('Semi', 4.9 * s); c.drawCentredString(lx + lw / 2, y + 2.2 * s, G.VILLA_TEL)


def patinhas_fundo(c, cor, y0=0, y1=PW, dens=1.0, semente=3):
    rng = np.random.default_rng(semente)
    n = int(26 * dens)
    for i in range(n):
        x = rng.uniform(0, PW); y = rng.uniform(y0, y1)
        G.pata(c, x, y, rng.uniform(4.5, 8), cor, rng.uniform(-40, 40))


# =================================================================== MODELO 1 - FOTO DO MES
def m1(c, mes):
    m = mes + 1
    c.setFillColor(BRANCO); c.rect(0, 0, PW, PW, stroke=0, fill=1)
    foto(c, mes, 0, 136, PW, V.WIRE - 136)
    # faixa dos furos do wire-o (rosa com patinhas)
    c.setFillColor(ROSA_BG); c.rect(0, V.WIRE, PW, PW - V.WIRE, stroke=0, fill=1)
    for x, y, a in [(18, 241, -20), (60, 250, 15), (128, 246, 0), (200, 251, -10), (243, 240, 20)]:
        G.pata(c, x, y, 6, CMYKColor(0, 0.13, 0.04, 0), a)
    c.setFillColor(ROSA); c.rect(0, V.WIRE - 1.5, PW, 1.5, stroke=0, fill=1)
    # borda ondulada branca sobre a foto
    c.setFillColor(BRANCO)
    p = c.beginPath(); p.moveTo(0, 128); p.lineTo(0, 146)
    p.curveTo(70, 132, 150, 158, PW, 140); p.lineTo(PW, 128); p.close(); c.drawPath(p, stroke=0, fill=1)
    # pilula do mes
    nome = V.MESES[mes]
    fs = 13
    w = pdfmetrics.stringWidth(nome, 'Black', fs) + pdfmetrics.stringWidth('  2027', 'Black', 9) + 18
    c.setFillColor(BRANCO); c.roundRect(12, 141, w + 3, 23, 11.5, stroke=0, fill=1)
    c.setFillColor(ROSA); c.roundRect(13.5, 142.5, w, 20, 10, stroke=0, fill=1)
    c.setFillColor(BRANCO); c.setFont('Black', fs); c.drawString(22, 148, nome)
    c.setFillColor(AMARELO); c.setFont('Black', 9); c.drawString(22 + pdfmetrics.stringWidth(nome + ' ', 'Black', fs), 148.6, '2027')
    est = dict(sem_pill=False, sem_txt=ROSA_ESC, sem_dom_txt=ROSA, sem_tam=5.2, sem_h=7,
               celula='ret', cel_bg=ROSA_BG, txt=MARROM, dom_txt=ROSA, fer_bg=ROSA, fer_txt=BRANCO,
               pet_bg=AMARELO, pet_txt=MARROM, fonte='XBold', fonte_dest='Black', lua='canto',
               tam_max=8.4, tam_rel=.66, raio=2.2)
    grade(c, m, 14, 248, 60, 133, est)
    legenda(c, m, 15, 247, 52.5)
    c.setFillColor(ROSA_BG); c.rect(0, 0, PW, 47, stroke=0, fill=1)
    c.setFillColor(ROSA); c.rect(0, 46, PW, 1.4, stroke=0, fill=1)
    marcas(c, 13, ROSA_BG)


# =================================================================== MODELO 2 - LADO A LADO
def m2(c, mes):
    m = mes + 1
    c.setFillColor(BRANCO); c.rect(0, 0, PW, PW, stroke=0, fill=1)
    meio = PW / 2
    # topo (area dos furos) em duas cores
    c.setFillColor(ROSA_BG); c.rect(0, V.WIRE, meio, PW - V.WIRE, stroke=0, fill=1)
    c.setFillColor(AMARELO_BG); c.rect(meio, V.WIRE, PW - meio, PW - V.WIRE, stroke=0, fill=1)
    # cabecalho dividido na diagonal
    hy0 = 168
    c.setFillColor(ROSA)
    p = c.beginPath(); p.moveTo(0, hy0); p.lineTo(meio - 14, hy0); p.lineTo(meio + 14, V.WIRE); p.lineTo(0, V.WIRE); p.close()
    c.drawPath(p, stroke=0, fill=1)
    c.setFillColor(AMARELO)
    p = c.beginPath(); p.moveTo(meio - 14, hy0); p.lineTo(PW, hy0); p.lineTo(PW, V.WIRE); p.lineTo(meio + 14, V.WIRE); p.close()
    c.drawPath(p, stroke=0, fill=1)
    # foto redonda no centro
    r = 33
    c.setFillColor(BRANCO); c.circle(meio, 197, r + 3, stroke=0, fill=1)
    foto(c, mes, meio - r, 197 - r, 2 * r, 2 * r, forma='circ')
    # mes (lado clinica) e ano (lado pet shop)
    nome = V.MESES[mes]
    fs = G.ajustar(c, nome, 'Black', 13, meio - r - 22)
    c.setFillColor(BRANCO); c.setFont('Black', fs); c.drawString(14, 199, nome)
    c.setFont('Med', 5.2); c.drawString(14.5, 190, 'Clínica Veterinária')
    c.setFont('Bold', 5.6); c.drawString(14.5, 183.5, 'Fernanda Calixto')
    c.setFillColor(MARROM); c.setFont('Black', 17); c.drawRightString(247, 199, '2027')
    c.setFont('Bold', 5.6); c.drawRightString(247, 190, 'VillaPet')
    c.setFont('Med', 5.2); c.drawRightString(247, 183.5, 'Pet Shop • Banho & Tosa')
    # faixa de servicos alternando por mes
    if mes % 2 == 0:
        txt, cor, bg = 'Consultas • Vacinas • Cirurgias • Internação', ROSA_ESC, ROSA_BG
    else:
        txt, cor, bg = 'Banho & Tosa • Rações • Acessórios • Petiscos', MARROM, AMARELO_BG
    c.setFillColor(bg); c.roundRect(14, 155, 234, 9.5, 4.75, stroke=0, fill=1)
    c.setFillColor(cor); c.setFont('Bold', 5.4); c.drawCentredString(PW / 2, 157.9, txt)
    est = dict(sem_pill=False, sem_txt=MARROM, sem_dom_txt=ROSA, sem_tam=5.3, sem_h=7.5,
               celula='ret', cel_bg=CMYKColor(0, 0.03, 0.03, 0.02), txt=MARROM, dom_txt=ROSA, fer_bg=ROSA, fer_txt=BRANCO,
               pet_bg=AMARELO, pet_txt=MARROM, fonte='XBold', fonte_dest='Black', lua='canto',
               tam_max=9.4, tam_rel=.62, raio=2.4)
    grade(c, m, 14, 248, 58, 152, est)
    legenda(c, m, 15, 247, 51)
    # rodape dividido
    c.setFillColor(ROSA_BG); c.rect(0, 0, meio, 46, stroke=0, fill=1)
    c.setFillColor(AMARELO_BG); c.rect(meio, 0, PW - meio, 46, stroke=0, fill=1)
    c.setFillColor(ROSA); c.rect(0, 45, meio, 1.5, stroke=0, fill=1)
    c.setFillColor(AMARELO); c.rect(meio, 45, PW - meio, 1.5, stroke=0, fill=1)
    G.selo_fernanda(c, 30, 26, 12, fundo=ROSA_BG)
    c.setFillColor(ROSA_ESC); c.setFont('Med', 4.2); c.drawString(46, 31, 'Clínica Veterinária')
    c.setFont('Black', 6.8); c.drawString(46, 24, 'Fernanda Calixto')
    c.setFillColor(MARROM); c.setFont('Semi', 4.9); c.drawString(46, 17.5, G.FER_TEL)
    G.imagem_cmyk(c, 'villapet.png', 155, 21.5, w=72, fundo=AMARELO_BG)
    c.setFillColor(MARROM); c.setFont('Semi', 4.9); c.drawCentredString(191, 14, G.VILLA_TEL)


# =================================================================== MODELO 3 - POLAROID
def m3(c, mes):
    m = mes + 1
    c.setFillColor(ROSA_BG); c.rect(0, 0, PW, PW, stroke=0, fill=1)
    patinhas_fundo(c, CMYKColor(0, 0.12, 0.035, 0), y0=120, y1=PW, dens=.7, semente=mes + 1)
    # polaroid inclinada
    c.saveState(); c.translate(186, 182); c.rotate(-5 if mes % 2 == 0 else 4)
    pw_, ph_ = 96, 108
    c.setFillColor(CMYKColor(0.2, 0.45, 0.3, 0.35)); c.rect(-pw_ / 2 + 1.6, -ph_ / 2 - 2, pw_, ph_, stroke=0, fill=1)
    c.setFillColor(BRANCO); c.rect(-pw_ / 2, -ph_ / 2, pw_, ph_, stroke=0, fill=1)
    foto(c, mes, -pw_ / 2 + 6, -ph_ / 2 + 21, pw_ - 12, pw_ - 12)
    c.setFillColor(ROSA_ESC); c.setFont('Bold', 6.2); c.drawCentredString(0, -ph_ / 2 + 7.5, LEGENDA_FOTO[mes])
    # fita adesiva
    c.setFillColor(AMARELO_BG); c.saveState(); c.translate(0, ph_ / 2); c.rotate(3); c.rect(-15, -5, 30, 10, stroke=0, fill=1); c.restoreState()
    c.restoreState()
    # mes e ano a esquerda
    nome = V.MESES[mes]
    fs = G.ajustar(c, nome, 'Black', 17, 106)
    c.setFillColor(ROSA); c.setFont('Black', fs); c.drawString(14, 196, nome)
    c.setFillColor(AMARELO_ESC); c.setFont('Black', 20); c.drawString(14, 175, '2027')
    G.pata(c, 24, 160, 9, ROSA, -15); G.pata(c, 40, 151, 7, ROSA_CLA, 10); G.pata(c, 56, 160, 5.5, AMARELO, -5)
    # cartao branco do calendario
    c.setFillColor(BRANCO); c.roundRect(10, 50, PW - 20, 70, 9, stroke=0, fill=1)
    est = dict(sem_pill=False, sem_txt=ROSA_ESC, sem_dom_txt=ROSA, sem_tam=5.0, sem_h=7,
               celula='circ', cel_bg=None, txt=MARROM, dom_txt=ROSA, fer_bg=ROSA, fer_txt=BRANCO,
               pet_bg=AMARELO, pet_txt=MARROM, fonte='Bold', fonte_dest='Black', lua='lado',
               tam_max=7.6, tam_rel=.62, pata_pet=False)
    grade(c, m, 16, 245, 60, 116, est)
    legenda(c, m, 18, 244, 53.5, tam=4.4)
    # rodape: cartao branco com as marcas
    c.setFillColor(BRANCO); c.roundRect(10, 8, PW - 20, 37, 9, stroke=0, fill=1)
    marcas(c, 13.5, BRANCO, x0=18, x1=244)


# =================================================================== MODELO 4 - MINIMALISTA
def m4(c, mes):
    m = mes + 1
    c.setFillColor(BRANCO); c.rect(0, 0, PW, PW, stroke=0, fill=1)
    # numero gigante do mes
    c.setFillColor(CMYKColor(0, 0.10, 0.03, 0)); c.setFont('Black', 78); c.drawString(8, 150, '%02d' % m)
    nome = V.MESES[mes]
    c.setFillColor(ROSA_ESC); c.setFont('Black', 15)
    c.drawString(16, 182, nome)
    c.setFillColor(ROSA); c.setFont('Med', 8); c.drawString(16.5, 170, '2 0 2 7')
    c.setStrokeColor(AMARELO); c.setLineWidth(1.4); c.line(16.5, 164, 44, 164)
    # foto redonda com anel
    cx, cy, r = 200, 180, 38
    c.setStrokeColor(ROSA_CLA); c.setLineWidth(.8); c.circle(cx + 4, cy - 3, r + 3, stroke=1, fill=0)
    foto(c, mes, cx - r, cy - r, 2 * r, 2 * r, forma='circ')
    c.setFillColor(AMARELO); c.circle(cx - r + 8, cy - r + 10, 6.5, stroke=0, fill=1)
    G.pata(c, cx - r + 8, cy - r + 9.5, 6, BRANCO, -10)
    # linha
    c.setStrokeColor(ROSA_CLA); c.setLineWidth(.5); c.line(16, 141, 246, 141)
    est = dict(sem_pill=False, sem_txt=CINZA, sem_dom_txt=ROSA, sem_tam=5.0, sem_fonte='Bold', sem_h=8,
               celula='circ', cel_bg=None, txt=CMYKColor(0.55, 0.60, 0.60, 0.55), dom_txt=ROSA, fer_bg=ROSA, fer_txt=BRANCO,
               pet_bg=AMARELO, pet_txt=MARROM, fonte='Med', fonte_dest='Bold', lua='lado',
               lua_cor=ROSA, tam_max=8.4, tam_rel=.6, pata_pet=False, gap=1)
    grade(c, m, 16, 246, 64, 138, est)
    c.setStrokeColor(ROSA_CLA); c.line(16, 60, 246, 60)
    legenda(c, m, 16, 246, 52.5, tam=4.5)
    # dica + marcas
    dica = V.DICAS[mes]; fs = G.ajustar(c, dica, 'Ita', 4.8, 230)
    c.setFillColor(CINZA); c.setFont('Ita', fs); c.drawCentredString(PW / 2, 44, dica)
    marcas(c, 10, BRANCO, x0=16, x1=246)


# =================================================================== MODELO 5 - ILUSTRADO (v2)
def m5(c, mes):
    V.pagina(c, 2027, mes)


MODELOS = [('Modelo1_FotoDoMes', m1), ('Modelo2_LadoALado', m2), ('Modelo3_Polaroid', m3),
           ('Modelo4_Minimalista', m4), ('Modelo5_Ilustrado', m5)]


def gerar(func, saida):
    tmp = saida + '.tmp'
    c = canvas.Canvas(tmp, pagesize=(PW, PW))
    for mes in range(12):
        func(c, mes); c.showPage()
    c.save()
    r = PdfReader(tmp); w = PdfWriter()
    for pg in r.pages:
        pg.trimbox = RectangleObject([B, B, B + T, B + T]); pg.bleedbox = RectangleObject([0, 0, PW, PW])
        w.add_page(pg)
    w.write(saida); os.remove(tmp)


if __name__ == '__main__':
    out = sys.argv[1]; os.makedirs(out, exist_ok=True)
    so = sys.argv[2:] or [n for n, _ in MODELOS]
    for nome, f in MODELOS:
        if nome in so or any(nome.startswith(s) for s in so):
            gerar(f, os.path.join(out, nome + '_wire-o_8.80x8.80.pdf')); print('ok', nome)
