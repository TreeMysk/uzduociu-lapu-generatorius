# main.py
import os
import random
import string
import unicodedata
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    Table, TableStyle, SimpleDocTemplate, Spacer, Paragraph, Image, Flowable, KeepTogether
)
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.pdfgen import canvas

from reportlab.lib.styles import ParagraphStyle

import re

# ---------- Nustatymai ----------
FONTS_DIR = Path("fonts")
IMAGES_DIR = Path("images")
OUT_DIR = Path("out")
FONT_NAME = "DejaVuSans"
FONT_FILE = FONTS_DIR / "DejaVuSans.ttf"

# Registruojame šriftą lietuviškoms raidėms
if not FONT_FILE.exists():
    print("⚠️  Dėmesio: nerastas fonts/DejaVuSans.ttf. Įkelk šriftą, kitaip LT raidės gali nerodytis.")
else:
    pdfmetrics.registerFont(TTFont(FONT_NAME, str(FONT_FILE)))

# Bendri puslapio dydžiai
puslapio_plotis, puslapio_aukstis = A4
marge = 50

# ---------- Pagalbinės funkcijos ----------
def ivesti_zodzius():
    print("Įveskite žodžius, atskirdami kableliais (pvz. varlė, vilkas, lapė):")
    ivestis = input("Žodžiai: ")
    return [z.strip() for z in ivestis.split(",") if z.strip()]

def strip_diacritics(s: str) -> str:
    # Paverčia „ąčęėįšųūž“ į „aceeis uuz“ failų paieškai
    return "".join(
        c for c in unicodedata.normalize("NFD", s)
        if unicodedata.category(c) != "Mn"
    )

def rasti_paveiksleli(zodis: str):
    """Ieško images/ kataloge failo pagal žodį:
       1) tiksliai su diakritikais (lowercase)
       2) be diakritikų (fallback)
    """
    candidates = []
    lower = zodis.lower()
    ascii_name = strip_diacritics(lower)
    for base in (lower, ascii_name):
        for ext in (".png", ".jpg", ".jpeg"):
            candidates.append(IMAGES_DIR / f"{base}{ext}")
    for p in candidates:
        if p.exists():
            return str(p)
    return None

# ---------- 1. Žodžių rašymo užduotis ----------
def generuoti_zodziu_uzduoti(zodziai, failas="out/uzduotis-zodziai.pdf"):
    OUT_DIR.mkdir(exist_ok=True)
    doc = SimpleDocTemplate(
        failas, pagesize=A4,
        leftMargin=marge, rightMargin=marge, topMargin=40, bottomMargin=40
    )
    st = getSampleStyleSheet()
    font = FONT_NAME if FONT_FILE.exists() else "Helvetica"
    st["Title"].fontName = font
    st["Normal"].fontName = font

    # Naujas stilius didesniam šriftui
    word_style = ParagraphStyle(
        "WordStyle",
        parent=st["Normal"],
        fontName=font,
        fontSize=80,
        leading=22
    )

    story = [Paragraph("Parašyk žodžius:", st["Title"]), Spacer(1, 12)]

    for z in zodziai:
        img_path = rasti_paveiksleli(z)
        img = Image(img_path, width=40, height=40) if img_path else Spacer(40, 40)

        # Eilutė su paveikslėliu ir žodžiu
        row1 = [img, Paragraph(z.capitalize(), st["Normal"])]
        table1 = Table([row1], colWidths=[50, 500])
        table1.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))

        # Linijos rašymui
        lines = WritingLines(width=500, height=30)

        story += [table1, lines, Spacer(1, 8)]

    doc.build(story)
    print(f"✅ PDF sukurtas: {failas}")

# ---------- 2. Žodžių paieška: tinklelis + paveikslėliai + 3 linijų forma ----------
def sugeneruoti_zodziu_paieskos_tinkla(zodziai, dydis=15):
    tinklelis = [["" for _ in range(dydis)] for _ in range(dydis)]
    for zodis in zodziai:
        U = zodis.upper()
        ilgis = len(U)
        for _ in range(200):  # daugiau bandymų dėl ilgesnių žodžių
            kryptis = random.choice(["H", "V"])
            if kryptis == "H":
                eil = random.randint(0, dydis - 1)
                stulp = random.randint(0, dydis - ilgis)
                if all(tinklelis[eil][stulp + i] in ["", U[i]] for i in range(ilgis)):
                    for i in range(ilgis):
                        tinklelis[eil][stulp + i] = U[i]
                    break
            else:  # Vertikaliai
                eil = random.randint(0, dydis - ilgis)
                stulp = random.randint(0, dydis - 1)
                if all(tinklelis[eil + i][stulp] in ["", U[i]] for i in range(ilgis)):
                    for i in range(ilgis):
                        tinklelis[eil + i][stulp] = U[i]
                    break
    # Užpildome likusius langelius
    for i in range(dydis):
        for j in range(dydis):
            if tinklelis[i][j] == "":
                tinklelis[i][j] = random.choice(string.ascii_uppercase)
    # Visi elementai -> str
    return [[str(ch) for ch in row] for row in tinklelis]

class WritingLines(Flowable):
    """Trijų eilučių „pirmos klasės“ rašymo forma: viršutinė pilna, vidurinė punktyrinė, apatinė pilna."""
    def __init__(self, width=260, gap=8, height=24, line_width=1):
        super().__init__()
        self.width = width
        self.gap = gap
        self.height = height  # bendras aukštis (nuo apatinės iki viršutinės)
        self.line_width = line_width

    def wrap(self, availWidth, availHeight):
        return (self.width, self.height)

    def draw(self):
        c = self.canv
        c.setLineWidth(self.line_width)
        apacia = 0
        vidurys = self.height / 2
        virsus = self.height
        # apatinė pilna
        c.setDash()
        c.line(0, apacia, self.width, apacia)
        # vidurinė punktyrinė
        c.setDash(1, 3)
        c.line(0, vidurys, self.width, vidurys)
        # viršutinė pilna
        c.setDash()
        c.line(0, virsus, self.width, virsus)

def generuoti_pdf_tinkleli_lentele(zodziai, dydis=15, failas="out/uzduotis-paieska.pdf"):
    OUT_DIR.mkdir(exist_ok=True)
    doc = SimpleDocTemplate(failas, pagesize=A4, leftMargin=marge, rightMargin=marge, topMargin=40, bottomMargin=40)
    st = getSampleStyleSheet()
    font = FONT_NAME if FONT_FILE.exists() else "Helvetica"
    st["Title"].fontName = font
    st["Normal"].fontName = font

    # 1) Tinklelis
    tinklelis = sugeneruoti_zodziu_paieskos_tinkla(zodziai, dydis=dydis)
    grid = Table(tinklelis, colWidths=20, rowHeights=20)
    grid.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTNAME', (0, 0), (-1, -1), font),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
    ]))

    story = []
    story.append(Paragraph("Rask žodžius tinklelyje", st["Title"]))
    story.append(Spacer(1, 12))
    story.append(grid)
    story.append(Spacer(1, 24))

    # 2) Paveikslėliai + trijų linijų forma PO DVI PORAS Į EILĘ
    pairs = []
    for z in zodziai:
        img_path = rasti_paveiksleli(z)
        img = Image(img_path, width=36, height=36) if img_path else Spacer(36, 36)

        # viena pora: [ikonėlė] [trijų linijų juosta]
        pair = Table([[img, WritingLines(width=220, height=26)]], colWidths=[42, 220])
        pair.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
            ('TOPPADDING', (0, 0), (-1, -1), 2),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        pairs.append(pair)

    # sudedame po 2 poras į vieną eilę (kad tilptų daugiau)
    for i in range(0, len(pairs), 2):
        left = pairs[i]
        right = pairs[i+1] if i+1 < len(pairs) else Spacer(262, 0)
        row = Table([[left, right]], colWidths=[262, 262])
        row.setStyle(TableStyle([
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
            ('TOPPADDING', (0, 0), (-1, -1), 0),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        story.append(row)

    doc.build(story)
    print(f"✅ PDF sukurtas: {failas}")

# ---------- 3. Linksnių lentelė ----------
def generuoti_linksniu_pdf_5k_vns_dgs(
    zodziai,
    failas="out/uzduotis-linksniai-5k-vns-dgs.pdf",
    rodyti_zodi_salia_paveikslelio=True
):
    OUT_DIR.mkdir(exist_ok=True)
    doc = SimpleDocTemplate(
        failas, pagesize=A4,
        leftMargin=marge, rightMargin=marge, topMargin=40, bottomMargin=40
    )
    st = getSampleStyleSheet()
    font = FONT_NAME if FONT_FILE.exists() else "Helvetica"
    st["Title"].fontName = font
    st["Normal"].fontName = font

    # ---- 2-eilių antraštė:  Žodis |  Vns. (kas ko kam kuo kur) | Dgs. (kas ko kam kuo kur)
    top_header = ["Žodis", "Vns.", "", "", "", "", "Dgs.", "", "", "", ""]
    sub_header = ["", "kas?", "ko?", "kam?", "kuo?", "kur?", "kas?", "ko?", "kam?", "kuo?", "kur?"]
    data = [top_header, sub_header]

    # ---- eilutės su žodžiais
    for z in zodziai:
        img_path = rasti_paveiksleli(z)
        img = Image(img_path, width=26, height=26) if img_path else Spacer(26, 26)

        if rodyti_zodi_salia_paveikslelio:
            first_cell = Table([[img, Paragraph(z.capitalize(), st["Normal"])]], colWidths=[28, 97])
            first_cell.setStyle(TableStyle([
                ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                ('LEFTPADDING', (0,0), (-1,-1), 0),
                ('RIGHTPADDING', (0,0), (-1,-1), 2),
            ]))
            first_w = 130
        else:
            first_cell = img
            first_w = 42

        row = [first_cell] + [""] * 10
        data.append(row)

    # ---- pločiai: ~495pt naudingo pločio
    rest_total = 495 - first_w
    each_w = max(34, int(rest_total / 10))  # 10 stulpelių „ką kam…“
    col_widths = [first_w] + [each_w] * 10

    t = Table(data, colWidths=col_widths, repeatRows=2)
    t.setStyle(TableStyle([
        # grotuotė ir šriftai
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ('FONTNAME', (0, 0), (-1, 1), font),
        ('FONTSIZE', (0, 0), (-1, 1), 11),
        ('ALIGN', (1, 2), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),

        # antraštės fonai
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
        ('BACKGROUND', (0, 1), (-1, 1), colors.whitesmoke),

        # sugrupavimų SPAN'ai
        ('SPAN', (0, 0), (0, 1)),    # „Žodis“ per dvi antraštės eilutes
        ('SPAN', (1, 0), (5, 0)),    # „Vns.“ per 5 stulpelius
        ('SPAN', (6, 0), (10, 0)),   # „Dgs.“ per 5 stulpelius

        # paraštės, kad būtų vietos rašymui
        ('TOPPADDING', (1, 2), (-1, -1), 10),
        ('BOTTOMPADDING', (1, 2), (-1, -1), 10),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
    ]))

    story = [Paragraph("Užpildyk: kas, ko, kam, kuo, kur — vns. ir dgs.", st["Title"]), Spacer(1, 10), t]
    doc.build(story)
    print(f"✅ PDF sukurtas: {failas}")


# ======= KRYŽIAŽODIS =======

# kryptys: dešinė (H), žemyn (V)
DIRS = [(0, 1, 'H'), (1, 0, 'V')]

def _fits(grid, r, c, w, dr, dc):
    """Ar žodis w telpa nuo (r,c) kryptimi (dr,dc) laikantis kryžiažodžio taisyklių?"""
    n = len(grid)
    L = len(w)

    # ribos
    if not (0 <= r + (L - 1) * dr < n and 0 <= c + (L - 1) * dc < n):
        return False

    # prieš ir po – siena/riba
    br, bc = r - dr, c - dc
    ar, ac = r + L * dr, c + L * dc
    if 0 <= br < n and 0 <= bc < n and grid[br][bc] not in ('', '#'):
        return False
    if 0 <= ar < n and 0 <= ac < n and grid[ar][ac] not in ('', '#'):
        return False

    for i, ch in enumerate(w):
        rr, cc = r + i * dr, c + i * dc
        cell = grid[rr][cc]
        if cell not in ('', ch):
            return False

        # be „prisiglaudimų“ iš šonų
        if dr == 0:  # horizontalus
            for sr, sc in ((-1, 0), (1, 0)):
                rr2, cc2 = rr + sr, cc + sc
                if 0 <= rr2 < n and 0 <= cc2 < n:
                    # išskyrus kraštinius simbolius ir jau esamą sutapimą
                    if grid[rr2][cc2] not in ('', '#') and (i != 0 and i != L - 1 or cell == ''):
                        return False
        else:        # vertikalus
            for sr, sc in ((0, -1), (0, 1)):
                rr2, cc2 = rr + sr, cc + sc
                if 0 <= rr2 < n and 0 <= cc2 < n:
                    if grid[rr2][cc2] not in ('', '#') and (i != 0 and i != L - 1 or cell == ''):
                        return False
    return True

def _place(grid, r, c, w, dr, dc):
    """Uždeda w, grąžina uždėtų langelių sąrašą (kad būtų galima nuimti)."""
    placed = []
    for i, ch in enumerate(w):
        rr, cc = r + i * dr, c + i * dc
        if grid[rr][cc] == '':
            grid[rr][cc] = ch
            placed.append((rr, cc))
    return placed

def _unplace(grid, placed):
    for r, c in placed:
        grid[r][c] = ''

def sugeneruoti_kryziazodi(words, size=13):
    """Sukuria kryžiažodį backtracking’u, skatinant susikirtimus."""
    words = [w.upper() for w in words]
    words.sort(key=len, reverse=True)  # ilgiausi – pirmi
    n = size
    grid = [['' for _ in range(n)] for _ in range(n)]
    placements = []  # (word, r, c, dr, dc)

    import random

    def score_positions(w):
        """Kandidatų sąrašas su balais (daugiau susikirtimų – geriau)."""
        cand = []
        for r in range(n):
            for c in range(n):
                for dr, dc, _ in DIRS:
                    if _fits(grid, r, c, w, dr, dc):
                        # paskaičiuojam kiek sutapimų su esamomis raidėmis
                        s = 0
                        for i, ch in enumerate(w):
                            rr, cc = r + i * dr, c + i * dc
                            if grid[rr][cc] == ch:
                                s += 1
                        cand.append(( -s, r, c, dr, dc))  # minus – kad sort būtų mažėjimo
        cand.sort()
        random.shuffle(cand[:3])  # truputį random, kad gautume įvairių maketų
        return cand

    def backtrack(k):
        if k == len(words):
            return True
        w = words[k]
        cands = score_positions(w)
        if not cands and k == 0:
            # pirmam žodžiui leiskime per centrą bet kuria kryptimi
            mid = n // 2
            cands = [(0, mid, max(0, mid - len(w) // 2), 0, 1),
                     (0, max(0, mid - len(w) // 2), mid, 1, 0)]

        for _, r, c, dr, dc in cands:
            put = _place(grid, r, c, w, dr, dc)
            placements.append((w, r, c, dr, dc))
            if backtrack(k + 1):
                return True
            placements.pop()
            _unplace(grid, put)
        return False

    backtrack(0)

    # neuždėti langeliai -> #
    for r in range(n):
        for c in range(n):
            if grid[r][c] == '':
                grid[r][c] = '#'
    return grid, placements

def numeruoti_pradzias(grid, placements):
    """
    Skenuoja tinklelį iš viršaus į apačią ir iš kairės į dešinę.
    Numeruoja tiek H, tiek V pradžias (atskirai).
    Grąžina:
      nums_map: {(r,c,'H'|'V'): nr}
      numbered: [(nr, word, r, c, dr, dc, 'H'|'V')] surikiuota pagal nr
    """
    n = len(grid)
    start2word = {}
    for w, r, c, dr, dc in placements:
        d = 'H' if dr == 0 else 'V'
        start2word[(r, c, d)] = w

    def is_block(rr, cc):
        return not (0 <= rr < n and 0 <= cc < n) or grid[rr][cc] == '#'

    nums_map = {}
    cur = 1
    for r in range(n):
        for c in range(n):
            if grid[r][c] == '#':
                continue
            if is_block(r, c - 1) and (r, c, 'H') in start2word:
                nums_map[(r, c, 'H')] = cur; cur += 1
            if is_block(r - 1, c) and (r, c, 'V') in start2word:
                nums_map[(r, c, 'V')] = cur; cur += 1

    numbered = []
    for (r, c, d), nr in nums_map.items():
        dr, dc = (0, 1) if d == 'H' else (1, 0)
        w = start2word[(r, c, d)]
        numbered.append((nr, w, r, c, dr, dc, d))
    numbered.sort(key=lambda x: x[0])
    return nums_map, numbered

def kryziazodis_pdf(words, show_answers=False, size=13, failas="out/kryziazodis.pdf"):
    """
    Sugeneruoja PDF:
      - kairėje: tinklelis su mažais numeriais starto langeliuose
      - dešinėje: sunumeruoti paveikslėliai (užuominos)
    """
    OUT_DIR.mkdir(exist_ok=True)
    grid, placements = sugeneruoti_kryziazodi(words, size=size)
    nums_map, numbered = numeruoti_pradzias(grid, placements)

    doc = SimpleDocTemplate(failas, pagesize=A4,
                            leftMargin=marge, rightMargin=marge,
                            topMargin=36, bottomMargin=36)
    st = getSampleStyleSheet()
    font = FONT_NAME if FONT_FILE.exists() else "Helvetica"
    for k in ("Title", "Normal"):
        st[k].fontName = font

    # --- tinklelis ---
    N = len(grid)
    cells = [['' for _ in range(N)] for _ in range(N)]
    ts = [
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTNAME', (0, 0), (-1, -1), font),
        ('FONTSIZE', (0, 0), (-1, -1), 12),
    ]
    small = ParagraphStyle("small", parent=st["Normal"],
                           fontName=font, fontSize=6, leading=7)

    for r in range(N):
        for c in range(N):
            if grid[r][c] == '#':
                ts.append(('BACKGROUND', (c, r), (c, r), colors.lightgrey))
                continue

            letter = grid[r][c] if show_answers else ''
            tags = []
            if (r, c, 'H') in nums_map: tags.append(nums_map[(r, c, 'H')])
            if (r, c, 'V') in nums_map: tags.append(nums_map[(r, c, 'V')])

            if tags:
                if show_answers and letter:
                    html = f'<para leading=7><font size="6">{" / ".join(map(str, tags))}</font><br/><font size="12">{letter}</font></para>'
                    cells[r][c] = Paragraph(html, st["Normal"])
                    ts += [('LEFTPADDING', (c, r), (c, r), 2),
                           ('TOPPADDING', (c, r), (c, r), 2)]
                else:
                    cells[r][c] = Paragraph(f'<font size="6">{" / ".join(map(str, tags))}</font>', small)
                    ts += [('LEFTPADDING', (c, r), (c, r), 2),
                           ('TOPPADDING', (c, r), (c, r), 2),
                           ('ALIGN', (c, r), (c, r), 'LEFT'),
                           ('VALIGN', (c, r), (c, r), 'TOP')]
            else:
                cells[r][c] = letter

    table = Table(cells, colWidths=20, rowHeights=20)
    table.setStyle(TableStyle(ts))

    # --- užuominos (paveikslėliai) ---
    hint_rows = []
    for nr, w, *_ in numbered:
        img_path = rasti_paveiksleli(w.lower())
        img = Image(img_path, width=40, height=40) if img_path else Spacer(40, 40)
        hint_rows.append([Paragraph(str(nr), st["Normal"]), img])

    hints = Table(hint_rows, colWidths=[18, 44])
    hints.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTNAME', (0, 0), (-1, -1), font),
    ]))

    layout = Table([[table, hints]], colWidths=[N * 20 + 10, 80])
    layout.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
    ]))

    story = [Paragraph("Išspręsk kryžiažodį", st["Title"]), Spacer(1, 8), layout]
    doc.build(story)
    print(f"✅ PDF sukurtas: {failas}")


# ---------- parašyk sakinį pagal pvz. ----------

def generuoti_sakini_pagal_pavyzdi(
    zodziai,
    pavyzdys_sakinys: str,
    pavyzdys_paveikslelis: str = "",
    failas="out/uzduotis-sakinys-pagal-pavyzdi.pdf"
):
    OUT_DIR.mkdir(exist_ok=True)

    doc = SimpleDocTemplate(
        failas, pagesize=A4,
        leftMargin=marge, rightMargin=marge,
        topMargin=36, bottomMargin=36
    )

    st = getSampleStyleSheet()
    font = FONT_NAME if FONT_FILE.exists() else "Helvetica"
    st["Title"].fontName = font
    st["Normal"].fontName = font

    title = Paragraph("Parašyk sakinį pagal pavyzdį", st["Title"])

    sample_style = ParagraphStyle(
        "SampleSentence",
        parent=st["Normal"],
        fontName=font,
        fontSize=22,
        leading=26,
        spaceAfter=0
    )

    # pavyzdžio paveikslėlis (pagal žodį images/ kataloge; jei neranda – tuščias tarpas)
    sample_img_path = rasti_paveiksleli(pavyzdys_paveikslelis) if pavyzdys_paveikslelis else None
    sample_img = Image(sample_img_path, width=42, height=42) if sample_img_path else Spacer(42, 42)

    # VIENA eilutė: [paveikslėlis] [pavyzdinis sakinys] [3 linijų juosta]
    # Naudingas plotis ~495pt (A4 - paraštės). Stulpelių sumą laikom ≤495.
    top_row = Table(
        [[
            sample_img,
            Paragraph(pavyzdys_sakinys, sample_style),
            WritingLines(width=215, height=30)  # linija tame pačiame aukštyje
        ]],
        colWidths=[50, 230, 215]
    )
    # Viršuje: paveikslėlis + pavyzdinis sakinys
    sample_row = Table([[sample_img, Paragraph(pavyzdys_sakinys, sample_style)]],
                       colWidths=[50, 500])
    sample_row.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))

    # Po pavyzdinio sakinio — tik tarpas, be linijų
    story = [
        title,
        Spacer(1, 8),
        sample_row,
        Spacer(1, 12)  # tiesiog tuščia vieta, be rašymo linijų
    ]

    # Toliau – sąrašas BE žodžių: [paveikslėlis] [3 linijų juosta]
    for z in zodziai:
        img_path = rasti_paveiksleli(z)
        img = Image(img_path, width=42, height=42) if img_path else Spacer(42, 42)

        row = Table([[img, WritingLines(width=500, height=30)]], colWidths=[50, 500])
        row.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        story.append(row)

    doc.build(story)
    print(f"✅ PDF sukurtas: {failas}")

# ---------- Gyvūnai ir jų gyvenamosios vietos (2 dalių lapas)a ----------

def _row_of_images(names, img_size=48, total_width=495, gap=10):
    """Sukuria vieną eilę su paveikslėliais, išlygintą į kairę, su pastoviais tarpais."""
    cells = []
    for nm in names:
        p = rasti_paveiksleli(nm)
        img = Image(p, width=img_size, height=img_size) if p else Spacer(img_size, img_size)
        cells.append(img)
    # suskaičiuojam stulpelių plotį taip, kad tilptų į ~495pt
    col_w = (total_width - gap * (len(cells) - 1)) / max(1, len(cells))
    t = Table([cells], colWidths=[col_w] * len(cells))
    t.setStyle(TableStyle([
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 0),
        ('TOPPADDING', (0,0), (-1,-1), 0),
        ('BOTTOMPADDING', (0,0), (-1,-1), 0),
    ]))
    return t

def generuoti_gyvunai_ir_vietos(
    gyvunai, vietos,
    failas="out/uzduotis-gyvunai-vietos.pdf",
    rasymo_eiluciu_kiekis=12
):
    OUT_DIR.mkdir(exist_ok=True)
    doc = SimpleDocTemplate(
        failas, pagesize=A4,
        leftMargin=marge, rightMargin=marge, topMargin=36, bottomMargin=36
    )
    st = getSampleStyleSheet()
    font = FONT_NAME if FONT_FILE.exists() else "Helvetica"
    st["Title"].fontName = font
    st["Normal"].fontName = font

    story = []

    # --- 1 dalis: Sujunk kas kur gyvena? ---
    story.append(Paragraph("Sujunk kas kur gyvena?", st["Title"]))
    story.append(Spacer(1, 6))
    story.append(_row_of_images(gyvunai, img_size=48))
    story.append(Spacer(1, 36))  # tarpas linijoms braižyti
    story.append(_row_of_images(vietos, img_size=48))
    story.append(Spacer(1, 18))

    # --- 2 dalis: Parašyk kas gyvena kur? ---
    story.append(Paragraph("Parašyk kas gyvena kur?", st["Title"]))
    story.append(Spacer(1, 6))

    # keliolika „pradinukų“ stiliaus eilučių
    for _ in range(rasymo_eiluciu_kiekis):
        story.append(WritingLines(width=495, height=22))
        story.append(Spacer(1, 6))

    doc.build(story)
    print(f"✅ PDF sukurtas: {failas}")

