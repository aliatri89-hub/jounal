"""Mantl Movie Journal, for reMarkable Paper Pure (1404x1872, portrait).

Backdrops: put images in backdrops/NN.jpg (NN = entry number, e.g. 01.jpg).
If a file is missing and the entry has a TMDB path, the script tries to
download it (works on a normal computer). Otherwise the frame stays blank.
"""
import math
import os
import urllib.request

from PIL import Image, ImageEnhance, ImageOps
from reportlab.lib.colors import Color, black, white
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

HERE = os.path.dirname(os.path.abspath(__file__))
for name, f in [("Marker", "PermanentMarker.ttf"),
                ("Barlow", "BarlowCondensed-Regular.ttf"),
                ("Barlow-Semi", "BarlowCondensed-SemiBold.ttf"),
                ("Barlow-Bold", "BarlowCondensed-Bold.ttf")]:
    pdfmetrics.registerFont(TTFont(name, os.path.join(HERE, "fonts", f)))

VOLUME = 1
OUT = f"Mantl Movie Journal - Vol {VOLUME}.pdf"

# (title, director, year, tmdb backdrop path or None)
NEW_RELEASES = [
    ("Digger", "Alejandro G. Iñárritu", "2026", "b7t3r39Oll5qPxBKzLZ8eHMBD7l"),
    ("The Social Reckoning", "Aaron Sorkin", "2026", "1eTUa8YDfq7WbrTrTsUuMfLZPk3"),
    ("You Can See Everything", "Nathan Fielder & Lance Oppenheim", "2026", "fnIcdPVaO4JAzfLhv8OVEqFK6a7"),
    ("Musk", "Alex Gibney", "2026", "rbF8b5NqcN5SprJmWz9CwGquMGa"),
    ("Clayface", "James Watkins", "2026", "pwWR1DRjoFxwdH0jI2elBdXTF1F"),
    ("The Further Mis-Adventures of Cliff Booth", "David Fincher", "2026", None),
    ("Wild Horse Nine", "Martin McDonagh", "2026", "phYik8dKyN85d2iB2K3CphCsugL"),
    ("Paper Tiger", "James Gray", "2026", "1VhgzeA0tBbd7GtAw1d2nL3UUBk"),
    ("Dune: Part Three", "Denis Villeneuve", "2026", "i5E9H7Ik0u61ylDDTbmUpTL3Yw"),
    ("Avengers: Doomsday", "Anthony & Joe Russo", "2026", "5ZjwGeiGGq11UpxhmZlOtGEO3Zt"),
]
# From Ali's Mantl watchlist: pre-2010, most recently added 20, in release order
RETRO = [
    ("Modern Times", "Charlie Chaplin", "1936", "kSlO1pHpwQfPQdgVPr7dJiJNtJ8"),
    ("Rope", "Alfred Hitchcock", "1948", "81LX4wktTXWEXjLNlkHTmJm7tRu"),
    ("The Third Man", "Carol Reed", "1949", "rLLhOCgAjuvlKmjUqVb7P1UAbUI"),
    ("Harakiri", "Masaki Kobayashi", "1962", "23XAzEpKuKUFLW2aWANbuNmqSvL"),
    ("The Night Strangler", "Dan Curtis", "1973", "4Pq4HbWGxHj0KGpzuYsQOYZyZ6"),
    ("Lady Snowblood", "Toshiya Fujita", "1973", "u2fkLndVDFA0ie4a8k6GpWWsm0N"),
    ("Phantom of the Paradise", "Brian De Palma", "1974", "8KgVSZglXRO9Z71rUnhVAvYEmu5"),
    ("Carrie", "Brian De Palma", "1976", "zwJFfKQdfiptK2GY6N8GkZFrAxJ"),
    ("The American Friend", "Wim Wenders", "1977", "h59F8NcFSlucTK7fUcndD9TB9jg"),
    ("The Driver", "Walter Hill", "1978", "qJiaKFJ25vElTeDgxOyU7QU5nGZ"),
    ("Valley Girl", "Martha Coolidge", "1983", "stTmJizMu8LklEIIkSu7NqHchdH"),
    ("Cobra", "George P. Cosmatos", "1986", "zPDpHMdbbE4O0TxVkMcgD6j2ImR"),
    ("Plain Clothes", "Martha Coolidge", "1988", "sysMIUEd7cd9kCL20H9XKiYnINS"),
    ("A Nightmare on Elm Street 4: The Dream Master", "Renny Harlin", "1988", "pfrU9uHNtDxa6U93Fm9o4sjudGU"),
    ("Buffalo '66", "Vincent Gallo", "1998", "oCcRRoalUWy83x3gqhCIl6pPUAi"),
    ("Peppermint Candy", "Lee Chang-dong", "1999", "d9LNlmhjihHAAP1vKCQJo57JQFX"),
    ("eXistenZ", "David Cronenberg", "1999", "epmwIWdQLouFJ8yx55quVvgnTKu"),
    ("Dancer in the Dark", "Lars von Trier", "2000", "vxvzf0cGtFY2Vpw5ULWumCIW6Ri"),
    ("Rejected", "Don Hertzfeldt", "2000", "qRgpl30lxdWfhJfd1YFJhpZJYVk"),
    ("Dogville", "Lars von Trier", "2003", "r3xsFBD1VTUusk393bBc7SsDUJe"),
]

# Off the List: open slots for films not planned above. Titles stay handwritten.
# To add a backdrop later, put its TMDB backdrop path in the slot (or drop an image
# at backdrops/NN.jpg) and rebuild. The page count never changes, so the new PDF
# can replace the old one on the Pure without losing ink.
OFF_LIST_SLOTS = 20
OFF_LIST = {
    # 31: "tmdbBackdropPathWithoutJpg",
}

# vertical crop position per entry: 0 = keep the top, 1 = keep the bottom (default 0.4)
CROP_TOP = {1: 0.12, 2: 0.08, 3: 0.35, 4: 0.0, 5: 0.4, 6: 0.25,
            7: 0.6, 8: 0.3, 9: 0.12, 10: 0.15}

W, H = 1404, 1872
L = 64
TAB_X = W - 112
CR = TAB_X - 30

INK = black
MID = Color(0.38, 0.38, 0.38)
RULE = Color(0.74, 0.74, 0.74)
SOFT = Color(0.88, 0.88, 0.88)

TABS = [("Index", "p_index"), ("Off List", "p_off"), ("Watchlist", "p_watch"), ("Year", "p_year")]


def Y(y):
    return H - y


def text(c, x, y, s, size=28, font="Barlow", color=INK, anchor="l", spacing=0):
    c.setFillColor(color)
    if spacing:
        c.saveState()
        t = c.beginText()
        t.setFont(font, size)
        t.setCharSpace(spacing)
        w = c.stringWidth(s, font, size) + spacing * (len(s) - 1)
        x0 = x if anchor == "l" else (x - w / 2 if anchor == "c" else x - w)
        t.setTextOrigin(x0, Y(y))
        t.textOut(s)
        c.drawText(t)
        c.restoreState()
        return
    c.setFont(font, size)
    {"l": c.drawString, "c": c.drawCentredString, "r": c.drawRightString}[anchor](x, Y(y), s)


def fit_size(c, s, font, size, max_w, min_size=20):
    while size > min_size and c.stringWidth(s, font, size) > max_w:
        size -= 2
    return size


def label(c, x, y, s, color=MID):
    text(c, x, y, s.upper(), 24, "Barlow-Semi", color, spacing=2.5)


def hline(c, x1, x2, y, color=RULE, lw=1.2):
    c.setStrokeColor(color)
    c.setLineWidth(lw)
    c.line(x1, Y(y), x2, Y(y))


def box(c, x, y, w, h, fill=None, stroke=INK, lw=2):
    c.setLineWidth(lw)
    if stroke is not None:
        c.setStrokeColor(stroke)
    if fill is not None:
        c.setFillColor(fill)
    c.rect(x, Y(y + h), w, h, stroke=1 if stroke is not None else 0, fill=1 if fill is not None else 0)


def link(c, x, y, w, h, dest):
    c.linkRect("", dest, (x, Y(y + h), x + w, Y(y)), relative=0, thickness=0)


def checkbox(c, x, y, s, size=28):
    box(c, x, y - 24, 26, 26, stroke=MID, lw=2)
    text(c, x + 38, y, s, size, "Barlow", MID)
    return x + 38 + c.stringWidth(s, "Barlow", size) + 30


def star(c, cx, cy, r):
    pts = []
    for i in range(10):
        a = math.pi / 2 + i * math.pi / 5
        rr = r if i % 2 == 0 else r * 0.45
        pts.append((cx + rr * math.cos(a), Y(cy) + rr * math.sin(a)))
    p = c.beginPath()
    p.moveTo(*pts[0])
    for pt in pts[1:]:
        p.lineTo(*pt)
    p.close()
    c.setStrokeColor(INK)
    c.setLineWidth(2.5 if r > 20 else 1.6)
    c.setLineJoin(1)
    c.drawPath(p, stroke=1, fill=0)
    if r > 20:
        c.setStrokeColor(RULE)
        c.setLineWidth(1.5)
        c.setDash(4, 5)
        c.line(cx, Y(cy) + r - 4, cx, Y(cy) - r * 0.8)
        c.setDash()


def tabs(c, active=None):
    th = 190
    for i, (name, dest) in enumerate(TABS):
        y = 64 + i * (th + 12)
        on = name == active
        box(c, TAB_X, y, 112, th, fill=INK if on else SOFT, stroke=None)
        c.saveState()
        c.translate(TAB_X + 66, Y(y + th / 2))
        c.rotate(90)
        c.setFillColor(white if on else INK)
        c.setFont("Barlow-Bold", 34)
        c.drawCentredString(0, 0, name.upper())
        c.restoreState()
        link(c, TAB_X, y, 112, th, dest)
    c.saveState()
    c.translate(TAB_X + 70, 120)
    c.rotate(90)
    c.setFillColor(INK)
    c.setFont("Marker", 44)
    c.drawString(0, 0, "Mantl")
    c.restoreState()


def page_heading(c, title, sub):
    text(c, L, 140, title, 84, "Marker")
    text(c, CR, 128, sub.upper(), 26, "Barlow-Semi", MID, "r", spacing=3)
    hline(c, L, CR, 172, INK, 3)


# ---------- backdrops ----------

def get_backdrop(num, path, frame_w, frame_h):
    os.makedirs(os.path.join(HERE, "backdrops"), exist_ok=True)
    src = None
    for ext in ("jpg", "jpeg", "png", "webp"):
        p = os.path.join(HERE, "backdrops", f"{num:02d}.{ext}")
        if os.path.exists(p):
            src = p
            break
    if src is None and path and not os.environ.get("NO_DOWNLOAD"):
        p = os.path.join(HERE, "backdrops", f"{num:02d}.jpg")
        try:
            urllib.request.urlretrieve(f"https://image.tmdb.org/t/p/w1280/{path}.jpg", p)
            src = p
        except Exception:
            src = None
    if src is None:
        return None
    im = Image.open(src).convert("RGB")
    # centre-crop to the frame ratio
    target = frame_w / frame_h
    w, h = im.size
    if w / h > target:
        nw = int(h * target)
        im = im.crop(((w - nw) // 2, 0, (w - nw) // 2 + nw, h))
    else:
        nh = int(w / target)
        top = int((h - nh) * CROP_TOP.get(num, 0.4))
        im = im.crop((0, top, w, top + nh))
    im = im.resize((int(frame_w), int(frame_h)), Image.LANCZOS)
    g = ImageOps.grayscale(im)
    g = ImageOps.autocontrast(g, cutoff=1)
    g = ImageEnhance.Contrast(g).enhance(1.1)
    return ImageReader(g)


def backdrop_frame(c, x, y, w, h, img=None):
    if img:
        c.drawImage(img, x, Y(y + h), w, h)
    else:
        box(c, x, y, w, h, fill=SOFT, stroke=None)
        c.setStrokeColor(RULE)
        c.setLineWidth(1.5)
        c.setDash(10, 10)
        c.rect(x + 30, Y(y + h - 30), w - 60, h - 60)
        c.setDash()
    c.saveState()
    for i in range(14):
        a = 0.10 * (1 - i / 14)
        c.setStrokeColor(Color(0, 0, 0, alpha=a))
        c.setLineWidth(6)
        c.rect(x + 3 + i * 6, Y(y + h - 3 - i * 6), w - 6 - i * 12, h - 6 - i * 12)
    c.restoreState()
    box(c, x, y, w, h, stroke=INK, lw=3)


def tape_label(c, x, y, num, kind):
    c.saveState()
    c.translate(x, Y(y))
    c.rotate(-3)
    c.setFillColor(white)
    c.setStrokeColor(INK)
    c.setLineWidth(2.5)
    c.rect(0, -92, 250, 92, stroke=1, fill=1)
    c.setLineWidth(1)
    c.setStrokeColor(RULE)
    c.line(14, -26, 236, -26)
    c.setFillColor(MID)
    c.setFont("Barlow-Semi", 18)
    c.drawString(16, -20, f"{kind}  ·  NO.")
    c.setFillColor(INK)
    c.setFont("Marker", 56)
    c.drawCentredString(125, -80, f"{num:03d}")
    c.restoreState()


# ---------- pages ----------

def entry_page(c, num, film, kind, backdrop=None):
    tabs(c)
    bx, by, bw = L, 64, CR - L
    bh = int(bw / 2.6)
    img = get_backdrop(num, film[3] if film else backdrop, bw, bh)
    backdrop_frame(c, bx, by, bw, bh, img)

    split = L + int((CR - L) * 0.68)

    y = by + bh + 112
    label(c, L, y - 62, "Title")
    tag = {"SCREENER": "New release", "RETRO": "Retro", "OFF": "Off the list"}[kind]
    text(c, CR, y - 62, f"NO. {num:03d}  ·  {tag.upper()}", 22, "Barlow-Semi", MID, "r", spacing=2.5)
    if film:
        size = fit_size(c, film[0], "Marker", 54, CR - L)
        text(c, L, y - 12, film[0], size, "Marker")
    hline(c, L, CR, y, INK, 3)

    y += 92
    label(c, L, y - 52, "Director")
    label(c, split, y - 52, "Year")
    if film:
        size = fit_size(c, film[1], "Barlow-Semi", 36, split - 30 - L)
        text(c, L, y - 10, film[1], size, "Barlow-Semi")
        text(c, split, y - 10, film[2], 36, "Barlow-Semi")
    hline(c, L, split - 30, y, INK, 1.6)
    hline(c, split, CR, y, INK, 1.6)

    y += 92
    label(c, L, y - 52, "Watched")
    hline(c, L, L + 300, y, INK, 1.6)
    label(c, L + 340, y - 52, "With")
    hline(c, L + 340, CR, y, INK, 1.6)

    y += 70
    bx2 = L
    for s in ["Cinema", "Home", "Festival", "Other"]:
        bx2 = checkbox(c, bx2, y, s)
    c.setStrokeColor(RULE)
    c.setLineWidth(1.5)
    c.line(bx2 - 6, Y(y + 6), bx2 - 6, Y(y - 30))
    bx2 += 24
    for s in ["First watch", "Rewatch"]:
        bx2 = checkbox(c, bx2, y, s)

    y += 78
    label(c, L, y + 8, "Rating")
    r = 36
    for i in range(5):
        star(c, L + 150 + r + i * (2 * r + 24), y, r)

    y += 104
    text(c, L, y, "Thoughts", 52, "Marker")
    hline(c, L, CR, y + 22, INK, 3)
    yy = y + 22 + 56
    while yy <= H - 64:
        hline(c, L, CR, yy)
        yy += 56


def index_page(c, entries):
    tabs(c, "Index")
    page_heading(c, f"Vol. {VOLUME}", f"{len(entries)} films")
    row_h = 50
    y = 230

    def section(y, title):
        text(c, L, y + 6, title, 40, "Marker")
        hline(c, L, CR, y + 22, INK, 2)
        return y + 22

    def row(y, num, film, dest):
        top = y
        y += row_h
        text(c, L + 4, y - 14, f"{num:03d}", 26, "Barlow-Bold", MID)
        if film:
            size = fit_size(c, film[0], "Barlow-Semi", 32, CR - L - 400)
            text(c, L + 90, y - 13, film[0], size, "Barlow-Semi")
        # mini rating stars + watched tick on the right
        for i in range(5):
            star(c, CR - 250 + i * 34, y - 24, 13)
        box(c, CR - 52, y - 38, 26, 26, stroke=MID, lw=2)
        hline(c, L, CR, y, RULE)
        link(c, L, top, CR - L - 280, row_h, dest)
        return y

    y = section(y, "New Releases")
    text(c, CR - 250 - 13, y - 34, "RATING", 18, "Barlow-Semi", MID)
    text(c, CR - 39, y - 34, "SEEN", 18, "Barlow-Semi", MID, "c")
    for i, (num, film, kind) in enumerate(entries):
        if kind != "SCREENER":
            continue
        y = row(y, num, film, f"e{num}")
    y += 60
    y = section(y, "Retro")
    for num, film, kind in entries:
        if kind != "RETRO":
            continue
        y = row(y, num, film, f"e{num}")


def off_list_page(c, slots):
    tabs(c, "Off List")
    page_heading(c, "Off the List", f"{len(slots)} open slots")
    row_h = 74
    y = 230
    text(c, L, y + 6, "Unplanned watches", 40, "Marker")
    text(c, CR - 250 - 13, y - 4, "RATING", 18, "Barlow-Semi", MID)
    text(c, CR - 39, y - 4, "SEEN", 18, "Barlow-Semi", MID, "c")
    y += 22
    hline(c, L, CR, y, INK, 2)
    for num in slots:
        top = y
        y += row_h
        text(c, L + 4, y - 16, f"{num:03d}", 26, "Barlow-Bold", MID)
        for i in range(5):
            star(c, CR - 250 + i * 34, y - 28, 13)
        box(c, CR - 52, y - 42, 26, 26, stroke=MID, lw=2)
        hline(c, L, CR, y, RULE)
        link(c, L, top, 80, row_h, f"e{num}")


def watchlist_page(c):
    tabs(c, "Watchlist")
    page_heading(c, "Watchlist", f"Up next · Vol. {VOLUME + 1}")
    y = 230
    gap = 64
    mid = L + (CR - L) // 2
    text(c, L, y + 6, "New Releases", 40, "Marker")
    text(c, mid + 20, y + 6, "Retro", 40, "Marker")
    y += 22
    hline(c, L, CR, y, INK, 2)
    yy = y + gap
    while yy <= H - 64:
        for x0, x1 in [(L, mid - 20), (mid + 20, CR)]:
            box(c, x0, yy - 34, 24, 24, stroke=MID, lw=2)
            hline(c, x0 + 40, x1, yy)
        yy += gap


def year_page(c):
    tabs(c, "Year")
    page_heading(c, "Year", "Top 10 · monthly tally")
    y = 230
    text(c, L, y + 6, "Top 10", 40, "Marker")
    hline(c, L, CR, y + 22, INK, 2)
    y += 22
    for i in range(10):
        y += 70
        text(c, L + 4, y - 16, f"{i + 1}", 40, "Marker", anchor="l")
        hline(c, L + 70, CR, y, RULE)
    y += 90
    text(c, L, y + 6, "Films per month", 40, "Marker")
    hline(c, L, CR, y + 22, INK, 2)
    y += 22
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
              "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    cols, cw = 3, (CR - L) // 3
    for i, m in enumerate(months):
        col, rowi = i % cols, i // cols
        x = L + col * cw
        yy = y + 30 + rowi * 110
        label(c, x, yy + 26, m, INK)
        box(c, x, yy + 40, cw - 30, 56, stroke=MID, lw=1.6)
    # total
    yy = y + 30 + 4 * 110 + 40
    label(c, L, yy + 26, "Total", INK)
    box(c, L, yy + 40, cw - 30, 56, stroke=INK, lw=2.5)


def build():
    entries = []
    for i, f in enumerate(NEW_RELEASES):
        entries.append((i + 1, f, "SCREENER"))
    for j, f in enumerate(RETRO):
        entries.append((len(NEW_RELEASES) + j + 1, f, "RETRO"))

    c = canvas.Canvas(os.path.join(HERE, OUT), pagesize=(W, H))
    c.setTitle(f"Mantl Movie Journal — Vol. {VOLUME}")
    c.setAuthor("Ali Atri")

    off = list(range(len(entries) + 1, len(entries) + OFF_LIST_SLOTS + 1))

    c.bookmarkPage("p_index"); index_page(c, entries); c.showPage()
    c.bookmarkPage("p_off"); off_list_page(c, off); c.showPage()
    c.bookmarkPage("p_watch"); watchlist_page(c); c.showPage()
    c.bookmarkPage("p_year"); year_page(c); c.showPage()
    for num, film, kind in entries:
        c.bookmarkPage(f"e{num}")
        entry_page(c, num, film, kind)
        c.showPage()
    for num in off:
        c.bookmarkPage(f"e{num}")
        entry_page(c, num, None, "OFF", OFF_LIST.get(num))
        c.showPage()
    c.save()
    print("wrote", OUT, "pages:", 4 + len(entries) + len(off))


if __name__ == "__main__":
    build()
