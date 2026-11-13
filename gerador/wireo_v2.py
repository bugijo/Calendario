# -*- coding: utf-8 -*-
"""
Calendario de mesa wire-o 2027 - layout proprio (v2)
Clinica Veterinaria Fernanda Calixto + VillaPet

Pagina: 8,8 x 8,8 cm + 2 mm de sangria. Topo (~1 cm) livre para os furos do wire-o.
Tudo em CMYK, sem transparencia (compativel com PDF/X-1a).

Uso: python3 wireo_v2.py <saida.pdf>
"""
import os, sys, calendar, math
from reportlab.pdfgen import canvas
from reportlab.lib.colors import CMYKColor
from reportlab.pdfbase import pdfmetrics
from pypdf import PdfReader, PdfWriter
from pypdf.generic import RectangleObject

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gerar as G   # fontes, cores, logos em CMYK, pegada

ROSA, ROSA_ESC, ROSA_CLA, ROSA_BG = G.ROSA, G.ROSA_ESC, G.ROSA_CLA, G.ROSA_BG
AMARELO, MARROM, BRANCO = G.AMARELO, G.MARROM, G.BRANCO
ROSA_PAD = CMYKColor(0.00, 0.13, 0.04, 0.00)        # pegadas do fundo
AMARELO_CLA = CMYKColor(0.00, 0.10, 0.45, 0.00)
CINZA_TXT = CMYKColor(0.30, 0.40, 0.40, 0.25)

PW = 261.5748          # pagina com sangria (pt)
B = 6.063              # sangria
T = 249.449            # corte (8,8 cm)
X0, X1 = B + 7, B + T - 7          # area util horizontal
WIRE = B + T - 27.5                # abaixo disto fica a area livre de furos

MESES = ['JANEIRO', 'FEVEREIRO', 'MARÇO', 'ABRIL', 'MAIO', 'JUNHO', 'JULHO',
         'AGOSTO', 'SETEMBRO', 'OUTUBRO', 'NOVEMBRO', 'DEZEMBRO']

# feriados nacionais (destaque rosa)
FERIADOS = {(1, 1): 'Confraternização Universal', (3, 26): 'Sexta-feira Santa', (4, 21): 'Tiradentes',
            (5, 1): 'Dia do Trabalho', (9, 7): 'Independência', (10, 12): 'N. Sra. Aparecida',
            (11, 2): 'Finados', (11, 15): 'Proclamação da República', (11, 20): 'Consciência Negra',
            (12, 25): 'Natal'}
# datas comemorativas (so na legenda)
COMEMORATIVAS = {(2, 9): 'Carnaval', (2, 10): 'Cinzas', (3, 8): 'Dia da Mulher', (3, 28): 'Páscoa',
                 (5, 9): 'Dia das Mães', (5, 27): 'Corpus Christi', (6, 12): 'Dia dos Namorados',
                 (8, 8): 'Dia dos Pais', (10, 12): 'Dia das Crianças'}
# datas pet (destaque amarelo com pegada)
PET = {(3, 14): 'Dia Nacional dos Animais', (8, 8): 'Dia Internacional do Gato',
       (8, 26): 'Dia do Cachorro', (9, 9): 'Dia do Médico-Veterinário',
       (10, 4): 'Dia Mundial dos Animais', (12, 5): '1 ano da nova VillaPet!'}
# fases da lua 2027 (horario de Brasilia) - conferidas com o gabarito da grafica
LUAS = {1: [(7, 'N'), (15, 'C'), (22, 'L'), (29, 'M')], 2: [(6, 'N'), (14, 'C'), (20, 'L'), (28, 'M')],
        3: [(8, 'N'), (15, 'C'), (22, 'L'), (29, 'M')], 4: [(6, 'N'), (13, 'C'), (20, 'L'), (28, 'M')],
        5: [(6, 'N'), (13, 'C'), (20, 'L'), (28, 'M')], 6: [(4, 'N'), (11, 'C'), (18, 'L'), (27, 'M')],
        7: [(4, 'N'), (10, 'C'), (18, 'L'), (26, 'M')], 8: [(2, 'N'), (9, 'C'), (17, 'L'), (24, 'M'), (31, 'N')],
        9: [(7, 'C'), (15, 'L'), (23, 'M'), (29, 'N')], 10: [(7, 'C'), (15, 'L'), (22, 'M'), (29, 'N')],
        11: [(6, 'C'), (14, 'L'), (20, 'M'), (28, 'N')], 12: [(6, 'C'), (13, 'L'), (20, 'M'), (27, 'N')]}

DICAS = [
    'Calor forte: água fresca sempre e passeios fora do sol do meio-dia.',
    'Carnaval: barulho e fogos assustam. Deixe seu pet seguro em casa.',
    'Pulgas e carrapatos: mantenha a prevenção em dia o ano todo.',
    'Check-up anual: prevenir é o melhor jeito de cuidar.',
    'Esfriou? Caminha quentinha e banho com secagem completa.',
    'Festa junina: cuidado com fogos e comidas da festa.',
    'Férias? Planeje com antecedência a estadia do seu pet.',
    'Vermífugo em dia protege seu pet e toda a família.',
    'Vacinas em dia: confira a carteirinha do seu pet.',
    'Banho e tosa regulares deixam pele e pelos saudáveis.',
    'Escovação dental previne tártaro e mau hálito.',
    'Dezembro Verde: adote, não abandone. Fogos? Proteja seu pet.',
]


# ------------------------------------------------------------------ ilustracoes vetoriais
def gato(c, cx, cy, s, cor, cor2):
    c.saveState(); c.translate(cx, cy); c.setFillColor(cor)
    p = c.beginPath(); p.moveTo(-0.62*s, 0.15*s); p.lineTo(-0.55*s, 0.78*s); p.lineTo(-0.15*s, 0.45*s); p.close()
    c.drawPath(p, stroke=0, fill=1)
    p = c.beginPath(); p.moveTo(0.62*s, 0.15*s); p.lineTo(0.55*s, 0.78*s); p.lineTo(0.15*s, 0.45*s); p.close()
    c.drawPath(p, stroke=0, fill=1)
    c.ellipse(-0.66*s, -0.55*s, 0.66*s, 0.52*s, stroke=0, fill=1)
    c.setFillColor(cor2)
    c.ellipse(-0.32*s, 0.02*s, -0.16*s, 0.2*s, stroke=0, fill=1)
    c.ellipse(0.16*s, 0.02*s, 0.32*s, 0.2*s, stroke=0, fill=1)
    p = c.beginPath(); p.moveTo(-0.08*s, -0.08*s); p.lineTo(0.08*s, -0.08*s); p.lineTo(0, -0.18*s); p.close()
    c.drawPath(p, stroke=0, fill=1)
    c.setStrokeColor(cor2); c.setLineWidth(0.05*s); c.setLineCap(1)
    for sx in (-1, 1):
        c.line(sx*0.22*s, -0.16*s, sx*0.62*s, -0.10*s); c.line(sx*0.22*s, -0.22*s, sx*0.60*s, -0.28*s)
    c.restoreState()


def cachorro(c, cx, cy, s, cor, cor2, orelha):
    c.saveState(); c.translate(cx, cy)
    c.setFillColor(orelha)
    c.saveState(); c.translate(-0.55*s, 0.2*s); c.rotate(-18); c.ellipse(-0.18*s, -0.5*s, 0.18*s, 0.32*s, stroke=0, fill=1); c.restoreState()
    c.saveState(); c.translate(0.55*s, 0.2*s); c.rotate(18); c.ellipse(-0.18*s, -0.5*s, 0.18*s, 0.32*s, stroke=0, fill=1); c.restoreState()
    c.setFillColor(cor); c.ellipse(-0.52*s, -0.58*s, 0.52*s, 0.58*s, stroke=0, fill=1)
    c.setFillColor(BRANCO); c.ellipse(-0.3*s, -0.55*s, 0.3*s, -0.08*s, stroke=0, fill=1)
    c.setFillColor(cor2)
    c.circle(-0.2*s, 0.12*s, 0.075*s, stroke=0, fill=1); c.circle(0.2*s, 0.12*s, 0.075*s, stroke=0, fill=1)
    c.ellipse(-0.12*s, -0.25*s, 0.12*s, -0.1*s, stroke=0, fill=1)
    c.setStrokeColor(cor2); c.setLineWidth(0.045*s); c.setLineCap(1)
    c.line(0, -0.25*s, 0, -0.36*s)
    c.arc(-0.14*s, -0.46*s, 0, -0.30*s, 200, 140); c.arc(0, -0.46*s, 0.14*s, -0.30*s, 200, 140)
    c.restoreState()


def osso(c, cx, cy, s, cor, ang=0):
    c.saveState(); c.translate(cx, cy); c.rotate(ang); c.setFillColor(cor)
    c.roundRect(-0.5*s, -0.1*s, s, 0.2*s, 0.08*s, stroke=0, fill=1)
    for x in (-0.5, 0.5):
        for y in (-0.13, 0.13):
            c.circle(x*s, y*s, 0.15*s, stroke=0, fill=1)
    c.restoreState()


def lua(c, cx, cy, r, fase, cor, fundo):
    c.setFillColor(cor); c.setStrokeColor(cor); c.setLineWidth(0.45)
    if fase == 'N':
        c.circle(cx, cy, r, stroke=0, fill=1)
    elif fase == 'L':
        c.setFillColor(fundo); c.circle(cx, cy, r, stroke=1, fill=1)
    else:
        c.setFillColor(fundo); c.circle(cx, cy, r, stroke=1, fill=1)
        c.saveState(); p = c.beginPath(); p.circle(cx, cy, r); c.clipPath(p, stroke=0, fill=0)
        c.setFillColor(cor)
        x = cx if fase == 'C' else cx - r
        c.rect(x, cy - r, r, 2*r, stroke=0, fill=1)
        c.restoreState()


# ------------------------------------------------------------------ pagina
def pagina(c, ano, mes):
    m = mes + 1
    # fundo geral
    c.setFillColor(BRANCO); c.rect(0, 0, PW, PW, stroke=0, fill=1)
    # area do wire-o: rosa claro com pegadas
    c.setFillColor(ROSA_BG); c.rect(0, WIRE, PW, PW - WIRE, stroke=0, fill=1)
    for i, (x, y, a) in enumerate([(16, 240, -20), (52, 250, 15), (210, 246, -10), (246, 238, 20), (128, 252, 0)]):
        G.pata(c, x, y, 6.5, ROSA_PAD, a)

    # cabecalho rosa com borda inferior arredondada
    hy0, hy1 = 190.0, WIRE
    c.setFillColor(ROSA)
    c.roundRect(-10, hy0, PW + 20, hy1 - hy0, 14, stroke=0, fill=1)
    c.rect(-10, hy0 + 14, PW + 20, hy1 - hy0 - 14, stroke=0, fill=1)
    c.setFillColor(AMARELO); c.rect(0, WIRE - 1.8, PW, 1.8, stroke=0, fill=1)
    # pegadas decorativas no cabecalho
    for x, y, s, a in [(150, 222, 6, -25), (163, 202, 4.5, 15), (176, 216, 3.6, -10)]:
        G.pata(c, x, y, s, CMYKColor(0.05, 0.70, 0.12, 0.0), a)
    # nome do mes e ano
    nome = MESES[mes]
    tam = G.ajustar(c, nome, 'Black', 21, 128)
    c.setFillColor(BRANCO); c.setFont('Black', tam); c.drawString(X0 + 2, 199.5, nome)
    # selo com ilustracao (alterna cao/gato)
    bx, by, br = X1 - 17, 205.5, 15.2
    c.setFillColor(BRANCO); c.circle(bx, by, br + 1.6, stroke=0, fill=1)
    c.setFillColor(AMARELO if mes % 2 == 0 else ROSA_BG); c.circle(bx, by, br, stroke=0, fill=1)
    if mes % 2 == 0:
        cachorro(c, bx, by - 0.5, 15.5, CMYKColor(0.15, 0.40, 0.65, 0.05), MARROM, MARROM)
    else:
        gato(c, bx, by - 1.5, 15.5, CMYKColor(0.0, 0.40, 0.75, 0.0), MARROM)
    # ano
    c.setFillColor(AMARELO); c.setFont('Black', 9.5); c.drawRightString(bx - br - 6, 199.8, '2027')

    # dias da semana
    cols = 7; gx0, gx1 = X0, X1
    cw = (gx1 - gx0) / cols
    wy = 178.5
    for i, l in enumerate('DSTQQSS'):
        cx = gx0 + cw * (i + 0.5)
        c.setFillColor(ROSA if i == 0 else (ROSA_BG if i < 6 else ROSA_BG))
        c.roundRect(cx - cw/2 + 1.2, wy - 1.6, cw - 2.4, 8.4, 4.2, stroke=0, fill=1)
        c.setFillColor(BRANCO if i == 0 else ROSA_ESC); c.setFont('Black', 5.6)
        c.drawCentredString(cx, wy + 0.4, l)

    # grade de dias
    cal = calendar.Calendar(firstweekday=6).monthdayscalendar(ano, m)
    nlin = len(cal)
    gy1, gy0 = wy - 4.0, 67.0
    rh = (gy1 - gy0) / nlin
    fases = dict(LUAS[m])
    for li, semana in enumerate(cal):
        for ci, d in enumerate(semana):
            if not d: continue
            x = gx0 + cw * ci; y = gy1 - rh * (li + 1)
            fer = (m, d) in FERIADOS; pet = (m, d) in PET
            if fer:
                fundo, txt = ROSA, BRANCO
            elif pet:
                fundo, txt = AMARELO, MARROM
            else:
                fundo, txt = (ROSA_BG, ROSA if ci == 0 else MARROM)
            c.setFillColor(fundo)
            c.roundRect(x + 1.0, y + 0.9, cw - 2.0, rh - 1.8, 3.2, stroke=0, fill=1)
            fs = min(11.5, rh * 0.62)
            c.setFillColor(txt); c.setFont('Black' if (fer or ci == 0 or pet) else 'XBold', fs)
            c.drawCentredString(x + cw / 2 - (1.6 if d in fases else 0), y + rh / 2 - fs * 0.36, str(d))
            if pet:
                G.pata(c, x + 5.0, y + rh - 5.0, 3.6, BRANCO, -15)
            if d in fases:
                lua(c, x + cw - 4.6, y + rh - 4.4, 1.9, fases[d], txt if (fer or pet) else MARROM, fundo)

    # legenda (feriados, comemorativas e datas pet)
    por_dia = {}
    for fonte in (FERIADOS, PET, COMEMORATIVAS):
        for (mm, d), t in fonte.items():
            if mm == m: por_dia.setdefault(d, []).append(t)
    partes = [('%02d %s' % (d, ' / '.join(por_dia[d])), (m, d) in PET and (m, d) not in FERIADOS)
              for d in sorted(por_dia)]
    if partes:
        larg = X1 - X0 - 2
        txt = '   '.join(p for p, _ in partes)
        fs = G.ajustar(c, txt, 'Semi', 5.0, larg)
        x = X0 + 1
        y = 60.2
        for i, (p, ehpet) in enumerate(partes):
            num, resto = p[:2], p[3:]
            c.setFillColor(ROSA if not ehpet else CMYKColor(0.0, 0.45, 0.95, 0.10)); c.setFont('Black', fs)
            c.drawString(x, y, num); x += pdfmetrics.stringWidth(num + ' ', 'Black', fs)
            c.setFillColor(CINZA_TXT); c.setFont('Semi', fs)
            c.drawString(x, y, resto); x += pdfmetrics.stringWidth(resto + '   ', 'Semi', fs)

    # rodape: dica + marcas
    c.setFillColor(ROSA_BG); c.rect(0, 0, PW, 56.5, stroke=0, fill=1)
    c.setFillColor(ROSA); c.rect(0, 45.5, PW, 11, stroke=0, fill=1)
    dica = DICAS[mes]
    t = G.ajustar(c, dica, 'Semi', 6.0, 214)
    G.pata(c, X0 + 4.5, 51.2, 6, AMARELO, -10)
    c.setFillColor(BRANCO); c.setFont('Semi', t); c.drawString(X0 + 11, 49.1, dica)
    G.selo_fernanda(c, 31, 27, 13, fundo=ROSA_BG)
    c.setFillColor(ROSA_ESC); c.setFont('Med', 4.6); c.drawString(48, 33.5, 'Clínica Veterinária')
    c.setFont('Black', 7.6); c.drawString(48, 25.6, 'Fernanda Calixto')
    c.setFillColor(MARROM); c.setFont('Semi', 5.2); c.drawString(48, 18.2, G.FER_TEL)
    c.setStrokeColor(ROSA_CLA); c.setLineWidth(0.7); c.line(134, 15, 134, 39)
    G.imagem_cmyk(c, 'villapet.png', 153, 20.5, w=72, fundo=ROSA_BG)
    c.setFillColor(MARROM); c.setFont('Semi', 5.2); c.drawCentredString(189, 12.6, G.VILLA_TEL)


def gerar(saida):
    tmp = saida + '.tmp'
    c = canvas.Canvas(tmp, pagesize=(PW, PW))
    c.setTitle('Calendário Wire-o 2027 - Fernanda Calixto + VillaPet')
    for mes in range(12):
        pagina(c, 2027, mes); c.showPage()
    c.save()
    r = PdfReader(tmp); w = PdfWriter()
    for pg in r.pages:
        pg.trimbox = RectangleObject([B, B, B + T, B + T]); pg.bleedbox = RectangleObject([0, 0, PW, PW])
        w.add_page(pg)
    w.add_metadata({'/Title': 'Calendário Wire-o 2027 - Fernanda Calixto + VillaPet'})
    w.write(saida); os.remove(tmp)


if __name__ == '__main__':
    gerar(sys.argv[1])
    print('ok')
