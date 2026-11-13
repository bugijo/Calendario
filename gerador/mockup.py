# -*- coding: utf-8 -*-
"""Gera uma imagem de referencia (mockup) do calendario wire-o montado na mesa.
Uso: python3 mockup.py <pagina_frente.png> <pagina_atras.png> <saida.png>"""
import sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

W, H = 2000, 1400


def coeffs(dst, src):
    """Coeficientes de Image.PERSPECTIVE que levam dst (saida) -> src (imagem)."""
    A, B = [], []
    for (x, y), (u, v) in zip(dst, src):
        A.append([x, y, 1, 0, 0, 0, -u * x, -u * y]); B.append(u)
        A.append([0, 0, 0, x, y, 1, -v * x, -v * y]); B.append(v)
    return np.linalg.solve(np.array(A, float), np.array(B, float)).tolist()


def colar(fundo, img, quad, sombra=0):
    iw, ih = img.size
    src = [(0, 0), (iw, 0), (iw, ih), (0, ih)]
    t = img.convert('RGBA').transform((W, H), Image.PERSPECTIVE, coeffs(quad, src), Image.BICUBIC)
    if sombra:
        t = Image.alpha_composite(t, Image.new('RGBA', (W, H), (0, 0, 0, 0)))
        a = np.array(t).astype(float); a[..., :3] *= (1 - sombra); t = Image.fromarray(a.astype('uint8'))
    fundo.alpha_composite(t)


def poligono(fundo, pts, cor, blur=0):
    camada = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(camada).polygon(pts, fill=cor)
    if blur: camada = camada.filter(ImageFilter.GaussianBlur(blur))
    fundo.alpha_composite(camada)


def main(frente, atras, saida):
    # fundo: mesa clara com degrade
    y = np.linspace(0, 1, H)[:, None]
    base = np.dstack([248 - 18 * y + 0 * np.ones((1, W)), 244 - 20 * y + 0 * np.ones((1, W)), 246 - 16 * y + 0 * np.ones((1, W))])
    img = Image.fromarray(base.clip(0, 255).astype('uint8')).convert('RGBA')

    # geometria (calendario em pe, visto de 3/4)
    TL, TR, BR, BL = (640, 330), (1290, 300), (1350, 1010), (590, 1050)     # pagina da frente
    back_bot_R, back_bot_L = (1560, 900), (900, 900)                          # pe de tras do cavalete

    # sombra no chao
    poligono(img, [(560, 1060), (1370, 1020), (1640, 920), (980, 905)], (60, 30, 50, 110), blur=28)

    # lateral do cavalete (triangulo de papelao branco)
    poligono(img, [TR, BR, back_bot_R], (226, 222, 226, 255))
    poligono(img, [TR, back_bot_R, (1300, 312)], (214, 210, 215, 255))
    # base / aba inferior
    poligono(img, [BL, BR, (1362, 1030), (580, 1072)], (236, 232, 236, 255))

    # folhas de tras (espessura do bloco) e a pagina da frente
    for i, d in enumerate([10, 7, 4]):
        poligono(img, [(TL[0] + d, TL[1] + d * 0.3), (TR[0] + d, TR[1] + d * 0.3),
                       (BR[0] + d, BR[1] + d * 0.2), (BL[0] + d, BL[1] + d * 0.2)], (238 - i * 4, 236 - i * 4, 238 - i * 4, 255))
    colar(img, Image.open(frente), [TL, TR, BR, BL])

    # leve sombreamento da pagina (luz vindo da esquerda)
    g = Image.new('L', (W, H), 0); ImageDraw.Draw(g).polygon([TL, TR, BR, BL], fill=255)
    ramp = Image.fromarray((np.linspace(0, 22, W)[None, :] * np.ones((H, 1))).astype('uint8'))
    escurecer = Image.new('RGBA', (W, H), (40, 20, 40, 0)); escurecer.putalpha(Image.composite(ramp, Image.new('L', (W, H), 0), g))
    img.alpha_composite(escurecer)

    # wire-o branco
    d = ImageDraw.Draw(img)
    n = 23
    for i in range(n):
        t = (i + 0.5) / n
        x = TL[0] + (TR[0] - TL[0]) * t; yb = TL[1] + (TR[1] - TL[1]) * t
        x0 = x - 7; y_top = yb - 34
        d.ellipse([x - 4, yb + 16, x + 4, yb + 24], fill=(70, 60, 70, 255))          # furo
        d.arc([x0 - 4, y_top, x0 + 18, yb + 26], start=180, end=360, fill=(150, 150, 155, 255), width=7)
        d.arc([x0 - 4, y_top, x0 + 18, yb + 26], start=180, end=360, fill=(252, 252, 252, 255), width=5)
        d.line([x0 + 18, yb - 4, x0 + 18, yb + 18], fill=(235, 235, 238, 255), width=4)

    img = img.convert('RGB')
    # miniatura de outro mes ao lado, como "pagina seguinte"
    if atras:
        mini = Image.open(atras).convert('RGB').resize((420, 420), Image.LANCZOS)
        moldura = Image.new('RGB', (440, 440), (255, 255, 255)); moldura.paste(mini, (10, 10))
        sh = Image.new('RGBA', (W, H), (0, 0, 0, 0)); ImageDraw.Draw(sh).rectangle([1515, 365, 1955, 805], fill=(0, 0, 0, 70))
        img = Image.alpha_composite(img.convert('RGBA'), sh.filter(ImageFilter.GaussianBlur(14))).convert('RGB')
        img.paste(moldura, (1500, 350))
    img.save(saida, quality=95)


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 3 else None, sys.argv[-1])
