# -*- coding: utf-8 -*-
"""
Arte da bandana pet (triangular) - VillaPet em destaque, Fernanda Calixto discreta.
Arte-mestre no tamanho G (66 x 25 cm) + 1 cm de sangria; escala para os outros tamanhos.
3 opcoes de cor unissex. CMYK, texto em curvas (pdfx).

Uso: python3 bandana.py <pasta_saida>
"""
import os, sys, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pdfx; pdfx.ativar()
import gerar as G
from reportlab.pdfgen import canvas
from reportlab.lib.colors import CMYKColor
from reportlab.pdfbase import pdfmetrics

CM = 28.3465
LARG, ALT, SANG = 66.0, 25.0, 1.0           # triangulo G (cm)
PW, PH = (LARG + 2 * SANG) * CM, (ALT + 2 * SANG) * CM
X0, Y0 = SANG * CM, SANG * CM                # canto inferior esquerdo da area final
W, H = LARG * CM, ALT * CM
TOPO_E, TOPO_D, PONTA = (X0, Y0 + H), (X0 + W, Y0 + H), (X0 + W / 2, Y0)

AMARELO, MARROM, BRANCO = G.AMARELO, G.MARROM, G.BRANCO
CREME = CMYKColor(0.0, 0.04, 0.14, 0.0)

OPCOES = {
    'Amarelo': dict(bg=AMARELO, pad=CMYKColor(0.0, 0.42, 1.0, 0.06), pad2=CMYKColor(0.0, 0.18, 0.75, 0.0),
                    costura=MARROM, selo=CREME, txt=MARROM),
    'Chocolate': dict(bg=MARROM, pad=CMYKColor(0.40, 0.52, 0.58, 0.28), pad2=CMYKColor(0.30, 0.42, 0.55, 0.15),
                      costura=AMARELO, selo=CREME, txt=CREME),
    'Creme': dict(bg=CREME, pad=AMARELO, pad2=CMYKColor(0.25, 0.35, 0.45, 0.10),
                  costura=MARROM, selo=BRANCO, txt=MARROM),
}


def osso(c, x, y, s, cor, ang):
    c.saveState(); c.translate(x, y); c.rotate(ang); c.setFillColor(cor)
    c.roundRect(-0.5 * s, -0.11 * s, s, 0.22 * s, 0.1 * s, stroke=0, fill=1)
    for dx in (-0.5, 0.5):
        for dy in (-0.13, 0.13):
            c.circle(dx * s, dy * s, 0.16 * s, stroke=0, fill=1)
    c.restoreState()


def coracao(c, x, y, s, cor, ang):
    c.saveState(); c.translate(x, y); c.rotate(ang); c.setFillColor(cor)
    p = c.beginPath(); p.moveTo(0, -0.5 * s)
    p.curveTo(-0.75 * s, 0, -0.45 * s, 0.6 * s, 0, 0.25 * s)
    p.curveTo(0.45 * s, 0.6 * s, 0.75 * s, 0, 0, -0.5 * s); p.close()
    c.drawPath(p, stroke=0, fill=1); c.restoreState()


def triangulo(c, margem=0.0):
    """Caminho do triangulo (margem > 0 expande para a sangria, < 0 contrai)."""
    m = margem
    # contrai/expande aproximado: desloca topo para cima/baixo e lados para fora/dentro
    k = H / math.hypot(W / 2, H)                      # seno do angulo do lado
    dx = m / k
    p = c.beginPath()
    p.moveTo(TOPO_E[0] - dx, TOPO_E[1] + m)
    p.lineTo(TOPO_D[0] + dx, TOPO_D[1] + m)
    p.lineTo(PONTA[0], PONTA[1] - m * math.hypot(W / 2, H) / (W / 2))
    p.close()
    return p


def arte(c, o):
    # fundo com sangria
    c.setFillColor(o['bg']); c.drawPath(triangulo(c, SANG * CM), stroke=0, fill=1)
    # estampa: patinhas, ossinhos e coracoes em grade intercalada
    c.saveState(); c.clipPath(triangulo(c, SANG * CM), stroke=0, fill=0)
    passo = 4.6 * CM
    i = 0
    y = Y0 - passo
    while y < PH + passo:
        x = -passo + (passo / 2 if i % 2 else 0)
        j = 0
        while x < PW + passo:
            ang = ((i * 7 + j * 13) % 5 - 2) * 12
            t = (i + j) % 3
            if t == 0:
                G.pata(c, x, y, 1.6 * CM, o['pad'], ang)
            elif t == 1:
                osso(c, x, y, 1.9 * CM, o['pad2'], ang + 30)
            else:
                coracao(c, x, y, 1.1 * CM, o['pad'], ang)
            x += passo; j += 1
        y += passo * 0.62; i += 1
    c.restoreState()
    # "costura" decorativa pontilhada nos lados
    c.saveState(); c.setStrokeColor(o['costura']); c.setLineWidth(0.09 * CM); c.setDash(0.35 * CM, 0.3 * CM)
    c.setLineCap(1)
    c.drawPath(triangulo(c, -0.9 * CM), stroke=1, fill=0)
    c.restoreState()
    # selo VillaPet (destaque) - area mais visivel quando amarrada
    lw = 15.5 * CM; lh = lw * 906 / 2627
    cx, cy = PONTA[0], Y0 + 14.2 * CM
    bw, bh = lw + 3.4 * CM, lh + 3.0 * CM
    borda = 0.2 * CM
    c.setFillColor(o['costura']); c.roundRect(cx - bw / 2 - borda, cy - bh / 2 - borda, bw + 2 * borda, bh + 2 * borda, bh / 2 + borda, stroke=0, fill=1)
    c.setFillColor(o['selo']); c.roundRect(cx - bw / 2, cy - bh / 2, bw, bh, bh / 2, stroke=0, fill=1)
    G.imagem_cmyk(c, 'villapet.png', cx - lw / 2, cy - bh / 2 + 1.85 * CM, w=lw, fundo=o['selo'])
    c.setFillColor(MARROM); c.setFont('Bold', 0.72 * CM)
    c.drawCentredString(cx, cy - bh / 2 + 0.85 * CM, '@villapet_  •  (16) 99311-4224')
    # Fernanda Calixto discreta, perto da ponta
    r = 0.95 * CM; fy = Y0 + 6.9 * CM
    c.setFillColor(o['bg']); c.roundRect(cx - 2.2 * CM, fy - r - 1.7 * CM, 4.4 * CM, 2 * r + 2.1 * CM, 1.2 * CM, stroke=0, fill=1)
    G.selo_fernanda(c, cx, fy, r, fundo=o['bg'])
    c.setFillColor(o['txt']); c.setFont('Semi', 0.5 * CM)
    c.drawCentredString(cx, fy - r - 0.75 * CM, 'Fernanda Calixto')
    c.setFont('Med', 0.38 * CM)
    c.drawCentredString(cx, fy - r - 1.3 * CM, 'Clínica Veterinária')

def gerar(out):
    os.makedirs(out, exist_ok=True)
    arqs = []
    for nome, o in OPCOES.items():
        f = os.path.join(out, f'Bandana_VillaPet_{nome}_G_66x25cm.pdf')
        c = canvas.Canvas(f, pagesize=(PW, PH))
        c.setTitle(f'Bandana VillaPet - {nome}')
        arte(c, o)
        c.showPage(); c.save()
        pdfx.finalizar(f, f + '.x', f'Bandana VillaPet - {nome}'); os.replace(f + '.x', f)
        arqs.append(f)
    return arqs


if __name__ == '__main__':
    for a in gerar(sys.argv[1]): print(a)
