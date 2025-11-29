# streamlit_book_recommender.py —  Nool Sakā “book-buddy”
# ---------------------------------------------------------------------------
# pastel wallpaper · interactive placeholders · enlarged QR listing all recos 1-N
# ranking: same-author → Indian-genre → Tamil-genre → Foreign-genre
# with SQLite logging of each lookup
# ---------------------------------------------------------------------------

from pathlib import Path
from typing import List
import difflib, io, pandas as pd, streamlit as st
from streamlit_searchbox import st_searchbox      # autosuggest component
import qrcode                                     # QR generator
from PIL import Image                             # for resizing
import sqlite3
from datetime import datetime
import base64

# ────────────────────────── 0 • PAGE STATE ───────────────────────────
if "page" not in st.session_state:
    st.session_state["page"] = "about"          # default landing screen

def goto_app():
    st.session_state["page"] = "app"

def goto_about():
    st.session_state["page"] = "about"

# ───────────────────────── A • DATABASE SETUP ───────────────────────────
__conn = sqlite3.connect("search_history.db", check_same_thread=False)
_cur  = __conn.cursor()

# DROP any existing (old) table
_cur.execute("DROP TABLE IF EXISTS search_log")

# Re-create with the new schema (no raw_input column)
_cur.execute("""
CREATE TABLE search_log (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp        TEXT    NOT NULL,
    book_name        TEXT    NOT NULL,
    author           TEXT    NOT NULL,
    genre            TEXT    NOT NULL,
    avg_rating       REAL    NOT NULL,
    total_ratings    INTEGER NOT NULL
)
""")
__conn.commit()

def log_search(row: pd.Series) -> None:
    """Insert one lookup record into SQLite."""
    ts = datetime.utcnow().isoformat()
    _cur.execute("""
        INSERT INTO search_log
          (timestamp, book_name, author, genre, avg_rating, total_ratings)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        ts,
        row["Book Name"],
        row["Author"],
        row["Genre"],
        float(row.get("Average Rating", 0)),
        int(row.get("Number of Ratings", 0))
    ))
    __conn.commit()

# ───────────────────────── 1 • PAGE STYLE ─────────────────────────
st.set_page_config(" Nalanda Labs", "📖", layout="wide")
st.markdown("""
<style>
html,body,.stApp {
  background: #FFF9C4;
  color: #111;
  font-family: 'Segoe UI', sans-serif;
}
body:before {
  content: '';
  position: fixed;
  inset: 0;
  background: url("data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjQiIGhlaWdodD0iMjQiIHZpZXdCb3g9IjAgMCAyNCAyNCI+PHBhdGggZmlsbD0iI0ZGRUIwMCIgZD0iTTcgMkgyMXYxOC03SDBaIi8+PC9zdmc+") repeat;
  opacity: .25;
  pointer-events: none;
  z-index: -2;
}
body:after {
  content: '';
  position: fixed;
  inset: 0;
  background: none;
  opacity: 0;
  pointer-events: none;
  z-index: -1;
}
.hero-main {
  position: relative;
  background: #FBC02D;   /* pastel yellow */
  color: #111;           /* near-black for readability */
  font-size: 2rem;
  font-weight: 800;
  text-align: center;
  padding: 0.6rem 0;
  margin: -2rem -2rem 0;
}
.hero-main:after {
  content: none;
}
.hero-sub {
  background: #FFFDE7;   /* pastel white/gray */
  color: #333;           /* soft black */
  font-family: 'Kalam', cursive;
  font-size: 1.8rem;
  font-weight: 600;
  text-align: center;
  padding: .6rem 0;
  margin: 0 -2rem;
}
.footer-credit {
  text-align: right;
  font-size: .95rem;
  font-weight: 600;
  color: #333;
  margin: .4rem 0 3rem;
}
section[data-testid="stSidebar"] > div:first-child {
  background: #ECEFF1;
}
.section-header {
  background: #A9A9A9;
  color: #000;
  padding: .8rem 1rem;
  font-weight: 600;
  border-radius: 10px;
}
.stDataFrame {
  background: #fff!important;
  border: 3px solid #FFC400;
  border-radius: 12px;
}
button[kind="primary"] {
  border-radius: 12px;
  font-weight: 800;
  background: #FFC400;
  border: none;
  color: #000;
  padding: .45rem 1.2rem;
}
button[kind="primary"]:hover {
  filter: brightness(110%);
  transform: translateY(-2px);
}
</style>
""", unsafe_allow_html=True)
import base64
from pathlib import Path

# 📌 Load the image and encode as base64
logo_path = Path("ChatGPT Image Jul 16, 2025, 08_09_35 PM.png")
if logo_path.exists():
    with open(logo_path, "rb") as f:
        logo_base64 = base64.b64encode(f.read()).decode()

    logo_img_tag = f"""
    <div class="hero-main" style="display: flex; align-items: center; justify-content: center; gap: 16px;">
        <img src="data:image/png;base64,{logo_base64}" 
             style="height:80px; margin-bottom:0;" />
        <span>NALANDA LABS</span>
    </div>
    """
else:
    logo_img_tag = '<div class="hero-main">NALANDA LABS</div>'

st.markdown(logo_img_tag, unsafe_allow_html=True)
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Kalam:wght@400;700&display=swap');
.hero-sub {
  background: #FFFDE7;  /* Lighter black */
  color: #333;
  font-family: 'Kalam', cursive;
  font-size: 1.8rem;
  font-weight: 600;
  text-align: center;
  padding: .6rem 0;
  margin: 0 -2rem;
}
</style>
<div class="hero-sub">Smart book recommendations. Zero overthinking.</div>
""", unsafe_allow_html=True)
celebrate = lambda: st.balloons()

# ────────────────────────── 3 • ABOUT PAGE ---------------------------
if st.session_state["page"] == "about":
    st.markdown("<h3>About Nalanda Labs</h3>", unsafe_allow_html=True)
    # Rich marketing copy
    st.markdown(
        """
        <div style="padding:1.2rem 1.5rem;max-width:900px;margin:auto;font-size:1.05rem;line-height:1.6;text-align:justify;">

<p><em>Tired of wandering through a book fair hoping the perfect title calls out to you telepathically?</em><br>
Yeah, us too.</p>

<p><strong>Nalanda Labs</strong> helps you cut the noise, skip the guilt‑buys, and discover books that match your <strong>actual reading personality</strong> — not some trending list made by a guy who’s read one novel and three tweets.We built Nalanda Labs so you could quietly answer a few smart questions and walk away with a <em>“how‑did‑you‑know‑I’d‑like‑this?”</em> recommendation.</p>

<p class="callout">You answer. We match. No complicated algorithms. Just clever ones.</p>

<p><strong>Step 1:</strong> Tap through 2‑3 books/authors you love<br>
<strong>Step 2:</strong> Get your personalised book stack<br>
<strong>Step 3:</strong> Screenshot it. Save it. Hunt it down at the fair.</p>

<p class="callout">“No queues. No fees. Just honest recommendations.”</p>

<p>All it takes is a few taps and 30 seconds. Your next favourite book might just be one screen away.
</div>
<style>
.callout{font-style:italic;font-weight:700;color:#BF9000;margin:1rem 0;text-align:center;}
</style>
        """,
        unsafe_allow_html=True,
    )
    st.button("👉 Try Us", on_click=goto_app, use_container_width=True)
    st.stop()

# ───────────────────────── 2 • DATA LOADER ───────────────────────
DEFAULT_PATH = Path("Book List1.csv")

@st.cache_data(show_spinner=False)
def load_dataset(path: Path) -> pd.DataFrame:
    def canonical(df: pd.DataFrame) -> pd.DataFrame:
        clean = {c.lower().replace(" ", "").replace("_", ""): c for c in df.columns}
        alias = lambda *alts: next((clean[a] for a in alts if a in clean), None)
        rename = {}
        for canon, alts in {
            "Book Name": ("bookname","book","title"),
            "Author":    ("author","authors"),
            "Genre":     ("genre","category")
        }.items():
            key = alias(*alts)
            if not key:
                raise ValueError(f"Missing {canon} column")
            rename[key] = canon

        rating = alias("averageratings","averagerating","avg")
        count  = alias("totalratings","numberofratings","ratingscount")
        nat    = alias("nationality","country","origin")

        if rating:
            rename[rating] = "Average Rating"
            df[rating] = pd.to_numeric(df[rating], errors="coerce").fillna(0).round(2)
        else:
            df["Average Rating"] = 0.0

        if count:
            rename[count] = "Number of Ratings"
            df[count] = pd.to_numeric(df[count], errors="coerce").fillna(0).astype(int)
        else:
            df["Number of Ratings"] = 0

        if nat:
            rename[nat] = "Nationality"

        return df.rename(columns=rename)

    raw = pd.read_excel(path) if path.suffix.lower()==".xlsx" else pd.read_csv(path, encoding="latin1")
    df  = canonical(raw).fillna("")
    df["_title_lc"]  = df["Book Name"].str.lower().str.strip()
    df["_author_lc"] = df["Author"].str.lower().str.strip()
    return df

# ───────────────────────── 3 • MATCH & RESOLVE ───────────────────
def resolve(df: pd.DataFrame, text: str) -> pd.Series:
    frag      = text.lower().strip()
    by_author = df[df["_author_lc"].str.contains(frag)]
    if not by_author.empty:
        row = by_author.iloc[0]
        log_search(row)
        return row

    by_title = df[df["_title_lc"].str.contains(frag)]
    if not by_title.empty:
        row = by_title.iloc[0]
        log_search(row)
        return row

    combos = (df["_title_lc"] + "|" + df["_author_lc"]).tolist()
    best   = difflib.get_close_matches(frag, combos, n=1, cutoff=0.3)
    if not best:
        st.error(f"No close match for '{text}'."); st.stop()

    row = df[(df["_title_lc"] + "|" + df["_author_lc"]) == best[0]].iloc[0]
    log_search(row)
    return row

# ───────────────────────── 4 • RECOMMENDER ───────────────────────
# Back‑arrow nav placed at top of the app view
st.markdown("<div style='text-align:left;'>", unsafe_allow_html=True)
st.button("← Back", on_click=goto_about, key="back_btn")
st.markdown("</div>", unsafe_allow_html=True)
def recommend(df: pd.DataFrame, favs: List[pd.Series], top: int = 10) -> pd.DataFrame:
    df = df.copy()
    df["Is Indian"] = df["Author"].str.lower().str.contains("|".join([
        "tagore","narayan","desai","nair","mistry","gosh","bhagat","murthy","rao","sahni"
    ]))
    df["Is Tamil"]  = df["Author"].str.lower().str.contains("|".join([
        "kalki","jeyamohan","vaasan","vairamuthu","sivashankari","sujatha",
        "imbam","charu","nivedita","imayam","magan","ananth","pandian"
    ]))

    fav_idx = {r.name for r in favs}
    authors = {r["Author"] for r in favs}
    genres  = {r["Genre"] for r in favs if r.get("Genre")}

    same_author = pd.concat([
        df[(df["Author"]==a)&(~df.index.isin(fav_idx))]
          .nlargest(3, ["Average Rating","Number of Ratings"])
        for a in authors
    ], ignore_index=False) if authors else pd.DataFrame()

    pool    = df[(df["Genre"].isin(genres)) & (~df.index.isin(fav_idx|set(same_author.index)))]
    indian  = pool[(pool["Is Indian"]) & (~pool["Is Tamil"])]
    tamil   = pool[pool["Is Tamil"]]
    foreign = pool[~pool["Is Indian"]]

    ranked = pd.concat([
        same_author,
        indian.nlargest(top,   ["Average Rating","Number of Ratings"]),
        tamil.nlargest(top,    ["Average Rating","Number of Ratings"]),
        foreign.nlargest(top,  ["Average Rating","Number of Ratings"]),
    ], ignore_index=False)

    if len(ranked) < top:
        rest = df[~df.index.isin(ranked.index)]
        ranked = pd.concat([
            ranked,
            rest[(rest["Is Indian"]) & (~rest["Is Tamil"])].nlargest(top, ["Average Rating","Number of Ratings"]),
            rest[rest["Is Tamil"]].nlargest(top, ["Average Rating","Number of Ratings"]),
            rest[~rest["Is Indian"]].nlargest(top, ["Average Rating","Number of Ratings"]),
        ], ignore_index=False)

    return ranked.drop_duplicates("Book Name").head(top)

# ───────────────────────── 5 • SIDEBAR & INPUTS ───────────────────
df = load_dataset(DEFAULT_PATH)
options = sorted(set(df["Book Name"]) | set(df["Author"]))

st.sidebar.header("🎯 1 | Pick how many recos")
rec_cnt = st.sidebar.slider("Suggestions wanted", 5, 25, 10, 1)
st.session_state["rec_cnt"] = rec_cnt
st.sidebar.markdown(
    f"<p style='margin-top:-0.5rem;'>🔢 "
    f"<span style='background:#FFC400;padding:2px 6px;border-radius:6px;font-weight:600'>{rec_cnt}</span> will be generated</p>",
    unsafe_allow_html=True,
)

st.sidebar.header("🎨 2 | Card tint")
card_color = st.sidebar.color_picker("Pick a light colour", "#F5F5F5")
st.session_state["card_color"] = card_color

def safe_rerun():
    if hasattr(st, "rerun"):
        st.rerun()
    else:
        st.experimental_rerun()

st.sidebar.header("🔄 3 | Start over")
if st.sidebar.button("Reset selections"):
    for key in ("favs_rows","favs_raw","recs_df","rec_idx","stored_rec_cnt","pick1","pick2","pick3"):
        st.session_state.pop(key, None)
    safe_rerun()

st.markdown('<div class="section-header">🤗 Hey buddy! Pick up to 3 books/authors you love:</div>', unsafe_allow_html=True)
def sugg(term: str) -> list[str]:
    return [o for o in options if term.lower() in o.lower()][:30] if term else []

favs = []
pick1 = st_searchbox(sugg, placeholder="🤔 What's got you hooked right now?", key="pick1")
if pick1:
    favs.append(pick1)
    pick2 = st_searchbox(sugg, placeholder="🔍 Got another fav? Share it!", key="pick2")
else:
    pick2 = None
if pick2:
    favs.append(pick2)
    pick3 = st_searchbox(sugg, placeholder="🎯 One last pick to seal the deal?", key="pick3")
else:
    pick3 = None
if pick3:
    favs.append(pick3)

st.markdown("""
<p style="
    text-align:center;
    font-size:0.95rem;
    font-weight:700;
    color:#555;
    margin-top:0.5rem;">
    The more you share, the sharper your recos become! 😉
</p>
""", unsafe_allow_html=True)

# ───────────────────────── 7 • ACTION & OUTPUTS ──────────────────
def build_qr_payload(df_out: pd.DataFrame) -> str:
    return "\n".join(
        f"{i}. {r['Book Name']} — {r['Author']} — Stall {r['Stall Number']}"
        for i, (_, r) in enumerate(df_out.iterrows(), 1)
    )[:4200]

def compute_recs():
    n_recs   = st.session_state.get("rec_cnt", 10)
    fav_rows = st.session_state.get("favs_rows", [])
    if not fav_rows:
        st.warning("Buddy, pick at least one favourite first!")
        return
    recs_df = (
        recommend(df, fav_rows, n_recs)
        [["Book Name", "Author", "Stall Number"]]
        .reset_index(drop=True)
    )
    st.session_state.update(recs_df=recs_df, stored_rec_cnt=n_recs, rec_idx=0)

if st.button("🚀 Get my recos!", use_container_width=True):
    st.session_state["favs_rows"] = [resolve(df, x) for x in favs]
    st.session_state["favs_raw"]  = favs
    compute_recs()
    celebrate()

# Recompute if slider changed
if st.session_state.get("recs_df") is not None and st.session_state.get("stored_rec_cnt") != rec_cnt:
    compute_recs()

# ───────── render ─────────
if "recs_df" in st.session_state:
    fav_rows   = st.session_state["favs_rows"]
    raw_picks  = st.session_state["favs_raw"]
    recs_df    = st.session_state["recs_df"]
    card_color = st.session_state.get("card_color", "#F5F5F5")

    st.markdown('<div class="section-header">✨ Your custom picks are here!</div>', unsafe_allow_html=True)
    st.markdown("""
    <style>
      div[data-testid="column"]:first-child{
          border-right:1px solid #BBB;
          margin-right:.5rem;padding-right:.5rem;}
    </style>""", unsafe_allow_html=True)

    left_pane, right_pane = st.columns([1, 2], gap="small")
    with left_pane:
        st.markdown(
            """<h2 style="
                font-size:1.6rem;
                background:#FFE082;
                padding:4px 10px;
                border-radius:6px;
                margin:0 0 .4rem 0;">
              Your picks
            </h2>""",
            unsafe_allow_html=True
        )
        for i, (raw, row) in enumerate(zip(raw_picks, fav_rows), 1):
            if raw.lower() in row["Author"].lower():
                st.write(f"{i}. **{row['Author']}**")
            else:
                st.write(f"{i}. **{row['Book Name']}**  \n{row['Author']}")

    with right_pane:
        VISIBLE, STEP = 3, 3
        total = len(recs_df)
        idx   = st.session_state.get("rec_idx", 0) % max(total, 1)
        end   = min(idx + VISIBLE, total)

        st.markdown(f"""
            <h3 style="
              font-size:1.6rem;
              background:#FFE082;
              padding:4px 10px;
              border-radius:6px;
              text-align:center;
              margin:0 0 .5rem 0;">
              📖 Showing {idx+1}–{end} of 🎉 {total} Recommendations
            </h3>""", unsafe_allow_html=True)

        prev_b, next_b = st.columns(2)
        with prev_b:
            st.button("◀ Prev", disabled=idx==0, use_container_width=True,
                      on_click=lambda: st.session_state.update(rec_idx=max(idx-STEP, 0)))
        with next_b:
            st.button("Next ▶", disabled=idx+STEP>=total, use_container_width=True,
                      on_click=lambda: st.session_state.update(rec_idx=min(idx+STEP, total-VISIBLE)))

        if st.session_state["rec_idx"] != idx:
            st.rerun()

        for _, row in recs_df.iloc[idx:end].iterrows():
            st.markdown(f"""
              <div style="
                background:{card_color};
                border-radius:8px;
                padding:0.6rem 0.8rem;
                margin-bottom:0.45rem;">
                <b>{row['Book Name']}</b><br>
                {row['Author']}<br>
                <small>Stall No: {row['Stall Number']}</small>
              </div>""", unsafe_allow_html=True)

        st.markdown("---")
        c1, c2 = st.columns(2, gap="small")
        with c1:
            st.download_button(
                "⬇️ CSV",
                recs_df.to_csv(index=False).encode(),
                "noolsaka_recs.csv",
                "text/csv"
            )
        with c2:
            qr = qrcode.QRCode(
                error_correction=qrcode.constants.ERROR_CORRECT_M,
                box_size=12,
                border=4
            )
            qr.add_data(build_qr_payload(recs_df))
            qr.make(fit=True)
            buf = io.BytesIO()
            qr.make_image(fill_color="black", back_color="white")\
               .resize((260, 260), Image.NEAREST).save(buf, "PNG")
            st.image(buf.getvalue(), caption="📱 Scan your list", width=260)
            st.download_button(
                "⬇️ QR PNG",
                buf.getvalue(),
                "noolsaka_recs.png",
                "image/png"
            )

# Optional: show history in the sidebar
ADMIN_PW = st.secrets.get("admin_password", "changeme")
with st.sidebar.expander("🔒 Admin login"):
    pw_input = st.text_input("Enter admin password", type="password")
    if pw_input and pw_input == ADMIN_PW:
        st.success("Authenticated as admin")
        df_hist = pd.read_sql(
            "SELECT id, timestamp, book_name, author "
            "FROM search_log ORDER BY id DESC LIMIT 100",
            _conn
        )
        st.dataframe(df_hist, hide_index=True)
    elif pw_input:
        st.error("Incorrect password")

