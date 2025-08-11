import io
import os
from pathlib import Path
import streamlit as st
from PIL import Image as PILImage

# mūsų modulis su ReportLab generatoriais
import worksheet as ws

st.set_page_config(page_title="Užduočių lapų generatorius", page_icon="📝", layout="centered")

st.title("📝 Užduočių lapų generatorius")

# --- bendri nustatymai / aplankai
IMAGES_DIR = ws.IMAGES_DIR
OUT_DIR = ws.OUT_DIR
IMAGES_DIR.mkdir(exist_ok=True)
OUT_DIR.mkdir(exist_ok=True)

def save_uploaded_any(file, preferred_basename: str | None = None):
    """
    Išsaugo įkeltą paveikslėlį kaip PNG (be vargo su JPEG alfa kanalu).
    Jei nurodytas preferred_basename, naudoja jį kaip failo pavadinimą.
    """
    img = PILImage.open(file)
    # jei yra alfa – paliekam RGBA, jei nėra – RGB
    if img.mode not in ("RGB", "RGBA"):
        img = img.convert("RGBA")
    base = preferred_basename or Path(file.name).stem
    target = IMAGES_DIR / f"{base}.png"
    img.save(target)   # visada .png
    return target

st.caption("Įkelkite paveikslėlius ir suveskite žodžius. PDF bus sugeneruotas vietoje ir bus galima parsisiųsti.")

tabs = st.tabs([
    "1) Žodžių sąrašas su eilutėmis",
    "2) Žodžių paieška",
    "3) Linksnių lentelė",
    "4) Kryžiažodis",
    "5) Sakinys pagal pavyzdį",
    "6) Gyvūnai ir jų vietos"
])

# ---- 1
with tabs[0]:
    st.subheader("Žodžių sąrašas su eilutėmis")
    words = st.text_input("Žodžiai (kableliais)", "kiškis, lapė, ežys")
    up = st.file_uploader("Paveikslėliai (pasirinkti keli; vardus sulyginsime su žodžiais)", type=["png","jpg","jpeg"], accept_multiple_files=True)
    # susiejimas: vartotojas net nebūtinai pervadins – mes pririšime pagal žodžių sąrašą žemiau
    st.caption("Patarimas: jei įkeltų failų vardai sutampa su žodžiais, nieko keisti nereikės.")

    if st.button("Generuoti PDF"):
        # išsaugom įkeltus failus pagal žodžių sąrašą, jei reikia – naudotojas gali įkelti vieną po kito
        # čia tiesiog išsaugom visus; paieška vyks per ws.rasti_paveiksleli
        for f in up:
            # saugom originaliu vardu (tavo rasti_paveiksleli su LT raidem tvarkosi)
            save_uploaded_any(f)

        zodziai = [w.strip() for w in words.split(",") if w.strip()]
        outfile = OUT_DIR / "uzduotis-zodziai.pdf"
        ws.generuoti_zodziu_uzduoti(zodziai, failas=str(outfile))
        st.success("PDF paruoštas.")
        st.download_button("Atsisiųsti PDF", data=open(outfile, "rb").read(), file_name=outfile.name, mime="application/pdf")

# ---- 2
with tabs[1]:
    st.subheader("Žodžių paieška (tinklelis + paveikslėliai + 3 linijų forma)")
    words = st.text_input("Žodžiai (kableliais)", "vilkas, lapė, meška")
    size = st.slider("Tinklelio dydis", 8, 20, 15)
    up = st.file_uploader("Paveikslėliai (nebūtina visiems)", type=["png","jpg","jpeg"], accept_multiple_files=True)
    if st.button("Generuoti paieškos PDF"):
        for f in up:
            save_uploaded_any(f)
        zodziai = [w.strip() for w in words.split(",") if w.strip()]
        outfile = OUT_DIR / "uzduotis-paieska.pdf"
        ws.generuoti_pdf_tinkleli_lentele(zodziai, dydis=size, failas=str(outfile))
        st.download_button("Atsisiųsti PDF", data=open(outfile, "rb").read(), file_name=outfile.name, mime="application/pdf")

# ---- 3
with tabs[2]:
    st.subheader("Linksnių lentelė")
    words = st.text_input("Žodžiai (kableliais)", "katė, šuo, pelė")
    up = st.file_uploader("Paveikslėliai (pasirinktinai)", type=["png","jpg","jpeg"], accept_multiple_files=True)
    if st.button("Generuoti linksnių PDF"):
        for f in up:
            save_uploaded_any(f)
        zodziai = [w.strip() for w in words.split(",") if w.strip()]
        outfile = OUT_DIR / "uzduotis-linksniai.pdf"
        ws.generuoti_linksniu_pdf(zodziai, failas=str(outfile))
        st.download_button("Atsisiųsti PDF", data=open(outfile, "rb").read(), file_name=outfile.name, mime="application/pdf")

# ---- 4
with tabs[3]:
    st.subheader("Kryžiažodis")
    words = st.text_input("Žodžiai (kableliais)", "arklys, kiškis, voverė, lapė")
    size = st.slider("Tinklelio dydis", 9, 17, 13)
    up = st.file_uploader("Paveikslėliai užuominoms", type=["png","jpg","jpeg"], accept_multiple_files=True)
    show_ans = st.checkbox("Sukurti ir atsakymų versiją", True)
    if st.button("Generuoti kryžiažodį"):
        for f in up:
            save_uploaded_any(f)
        zodziai = [w.strip() for w in words.split(",") if w.strip()]
        out1 = OUT_DIR / "kryziazodis.pdf"
        ws.kryziazodis_pdf(zodziai, show_answers=False, size=size, failas=str(out1))
        st.download_button("Atsisiųsti (tuščias)", data=open(out1, "rb").read(), file_name=out1.name, mime="application/pdf")
        if show_ans:
            out2 = OUT_DIR / "kryziazodis-atsakymai.pdf"
            ws.kryziazodis_pdf(zodziai, show_answers=True, size=size, failas=str(out2))
            st.download_button("Atsisiųsti (atsakymai)", data=open(out2, "rb").read(), file_name=out2.name, mime="application/pdf")

# ---- 5
with tabs[4]:
    st.subheader("Sakinys pagal pavyzdį")
    words = st.text_input("Žodžių sąrašas (kableliais)", "vilkas, lapė, meška")
    sample_sentence = st.text_input("Pavyzdinis sakinys", "Paukštis gyvena inkile.")
    sample_img_word = st.text_input("Kokio žodžio paveikslėlį naudoti pavyzdyje? (nebūtina)", "")
    up = st.file_uploader("Paveikslėliai (visi)", type=["png","jpg","jpeg"], accept_multiple_files=True)
    if st.button("Generuoti užduotį"):
        for f in up:
            save_uploaded_any(f)
        zodziai = [w.strip() for w in words.split(",") if w.strip()]
        outfile = OUT_DIR / "uzduotis-sakinys.pdf"
        ws.generuoti_sakini_pagal_pavyzdi(zodziai, pavyzdys_sakinys=sample_sentence, pavyzdys_paveikslelis=sample_img_word, failas=str(outfile))
        st.download_button("Atsisiųsti PDF", data=open(outfile, "rb").read(), file_name=outfile.name, mime="application/pdf")

# ---- 6
with tabs[5]:
    st.subheader("Gyvūnai ir jų gyvenamosios vietos (2 dalių lapas)")
    gyv = st.text_input("Gyvūnai (kableliais)", "paukštis, ežys, ožka, arklys, vilkas, šernas, lapė, karvė, voverė, varlė, kiškis, kiaulė")
    places = st.text_input("Vietos (kableliais)", "medžio drevė, tvenkinys, tvartas, inkilas, miškas")
    write_lines = st.slider("Rašymo eilučių kiekis", 6, 18, 12)
    up = st.file_uploader("Paveikslėliai (gyvūnai ir vietos, gali būti mišriai)", type=["png","jpg","jpeg"], accept_multiple_files=True)

    if st.button("Generuoti „Sujunk + Parašyk“ PDF"):
        for f in up:
            save_uploaded_any(f)
        gyvunai = [w.strip() for w in gyv.split(",") if w.strip()]
        vietos = [w.strip() for w in places.split(",") if w.strip()]
        outfile = OUT_DIR / "uzduotis-gyvunai-vietos.pdf"
        ws.generuoti_gyvunai_ir_vietos(gyvunai, vietos, failas=str(outfile), rasymo_eiluciu_kiekis=write_lines)
        st.download_button("Atsisiųsti PDF", data=open(outfile, "rb").read(), file_name=outfile.name, mime="application/pdf")