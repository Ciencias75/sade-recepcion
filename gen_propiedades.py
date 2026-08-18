import io, os, re, time, json, urllib.request, html as H
from urllib.parse import urlsplit

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36")
HERE = os.path.dirname(os.path.abspath(__file__))
SITE = "https://ciencias75.github.io/sade-recepcion"

def fetch(url, tries=3):
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={
                "User-Agent": UA,
                "Accept": "text/html,application/xhtml+xml",
                "Accept-Language": "es-MX,es;q=0.9"})
            with urllib.request.urlopen(req, timeout=30) as r:
                return r.read().decode("utf-8", "replace")
        except Exception:
            time.sleep(2)
    return ""

SMALL = {"en", "de", "la", "el", "los", "las", "del", "a", "y", "por", "al", "con", "para", "o", "e"}

def title_from_slug(slug):
    parts = slug.split("-")
    if len(parts) > 1 and re.fullmatch(r"[A-Za-z0-9]{6,8}", parts[-1]):
        parts = parts[:-1]
    return " ".join(p if p in SMALL else p.capitalize() for p in parts)

CITY_STATE = [
    ("bahia-de-banderas", "Bahía de Banderas, Nayarit"),
    ("tlajomulco-de-zuniga", "Tlajomulco de Zúñiga, Jalisco"),
    ("jocotepec", "Jocotepec, Jalisco"),
    ("tapalpa", "Tapalpa, Jalisco"),
    ("el-arenal", "El Arenal, Jalisco"),
    ("el-salto", "El Salto, Jalisco"),
    ("tonala", "Tonalá, Jalisco"),
    ("zapopan", "Zapopan, Jalisco"),
    ("guadalajara", "Guadalajara, Jalisco"),
]

def locate(slug):
    for k, v in CITY_STATE:
        if k in slug:
            return v
    return "Guadalajara y Zapopan, Jalisco"

def price_from_ogtitle(og):
    m = re.search(r"\$\s?([0-9][0-9']*(?:[,'][0-9]{3})*)\s*(?:PESOS|MXN)", og, re.I)
    if not m:
        return ""
    digits = m.group(1).replace("'", "").replace(",", "")
    try:
        return "$" + "{:,}".format(int(digits)) + " MXN"
    except ValueError:
        return ""

def extract_img(doc):
    ogimg = re.search(r'property="og:image" content="([^"]*)"', doc, re.I)
    if ogimg and ogimg.group(1).strip():
        return ogimg.group(1).strip()
    imgs = re.findall(r'<img[^>]+src="(https://media\.wiggot\.mx/[^"]+)"', doc, re.I)
    if not imgs:
        imgs = re.findall(r'(?:srcset|data-src)="([^"]*media\.wiggot\.mx[^"]*)"', doc, re.I)
    for c in imgs:
        f = c.split(",")[0].strip().split(" ")[0]
        if f and "iy5iu5w" not in f:
            return f
    return ""

def tipo_de(slug):
    for t in ("departamento", "terreno", "oficina", "bodega", "casa"):
        if slug.startswith(t):
            return t.capitalize()
    return "Propiedad"

def oferta_de(slug):
    return "Renta" if "en-renta" in slug else "Venta"
CSS = """
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:"Mulish",system-ui,sans-serif;background:#f4f4f1;color:#1c2a33;line-height:1.55}
a{color:inherit;text-decoration:none}
.wrap{max-width:1080px;margin:0 auto;padding:0 1rem}
.mini{background:#0f2324;display:flex;justify-content:space-between;align-items:center;padding:.7rem 1rem}
.mini img{display:block;height:34px;width:auto;background:#fff;padding:.25rem .5rem}
.pill{background:#7FC6BE;color:#fff;font-weight:700;font-size:.85rem;padding:.5rem .9rem;border-radius:999px}
.crumbs{font-size:.82rem;color:#5a6670;margin:1rem 0}
.crumbs a{color:#0f6f68;font-weight:600}
main{padding:0 1rem 2rem}
h1{font-size:clamp(1.5rem,4vw,2.3rem);font-weight:800;color:#0f2324;margin-bottom:.4rem}
.type{color:#0f6f68;font-weight:700;text-transform:uppercase;letter-spacing:.05em;font-size:.82rem;margin-bottom:.7rem}
.price{font-size:1.6rem;font-weight:800;color:#0f6f68;margin-bottom:1rem}
.photo{width:100%;max-height:460px;object-fit:cover;border-radius:10px;margin-bottom:1.1rem;background:#ddd}
.desc{background:#fff;border:1px solid #e3e3dd;border-radius:10px;padding:1.1rem 1.2rem;font-size:.95rem;margin-bottom:1.1rem}
.ctas{display:flex;flex-wrap:wrap;gap:.6rem;margin-bottom:1.5rem}
.cta{background:#0f6f68;color:#fff;font-weight:700;padding:.8rem 1.1rem;border-radius:8px;font-size:.92rem}
.cta.ghost{background:#fff;color:#0f6f68;border:1.5px solid #0f6f68}
footer{background:#0f2324;color:rgba(255,255,255,.85);padding:1.1rem 1rem;font-size:.85rem}
footer a{color:#9fd8d1;font-weight:600}
footer .wrap p{margin:.15rem 0;word-break:break-all}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(250px,1fr));gap:1rem;margin:1.4rem 0 2rem}
.card{background:#fff;border-radius:10px;overflow:hidden;border:1px solid #e3e3dd;display:flex;flex-direction:column;transition:transform .15s ease,box-shadow .15s ease}
.card:hover{transform:translateY(-2px);box-shadow:0 10px 24px rgba(15,35,36,.14)}
.card img{width:100%;height:150px;object-fit:cover;background:#ddd}
.card-body{padding:.85rem .95rem 1rem;display:flex;flex-direction:column;gap:.35rem;flex:1}
.badge{align-self:flex-start;background:#0f6f68;color:#fff;font-size:.7rem;font-weight:700;padding:.18rem .55rem;border-radius:999px;text-transform:uppercase;letter-spacing:.04em}
.card h2{font-size:.98rem;font-weight:700;color:#0f2324;line-height:1.3}
.card .p2{color:#0f6f68;font-weight:800}
.card .loc{color:#5a6670;font-size:.8rem}
.intro{background:#fff;border:1px solid #e3e3dd;border-radius:10px;padding:1rem 1.2rem;font-size:.95rem;margin-top:1.1rem}
.intro h2{font-size:1.05rem;color:#0f2324;margin-bottom:.4rem}
"""
import os, re, time, urllib.request, json
from datetime import date

SITE = "https://ciencias75.github.io/sade-recepcion"
LOGO_ID = "iy5iu5w"
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"}
SMALL = {"en", "de", "la", "el", "los", "las", "del", "a", "y", "por", "al", "con", "para", "e", "o"}
CITY_STATE = {
    "bahia-de-banderas": ("Bahía de Banderas, Nayarit", "bahia de banderas"),
    "tlajomulco-de-zuniga": ("Tlajomulco de Zúñiga, Jalisco", "tlajomulco"),
    "jocotepec": ("Jocotepec, Jalisco", "jocotepec"),
    "tapalpa": ("Tapalpa, Jalisco", "tapalpa"),
    "el-arenal": ("El Arenal, Jalisco", "el arenal"),
    "el-salto": ("El Salto, Jalisco", "el salto"),
    "tonala": ("Tonalá, Jalisco", "tonalá"),
    "zapopan": ("Zapopan, Jalisco", "zapopan"),
    "guadalajara": ("Guadalajara, Jalisco", "guadalajara"),
}
DEFAULT_LOC = ("Guadalajara y Zapopan, Jalisco", "Guadalajara y Zapopan")

def fmt_price(s):
    m = re.search(r"\$[0-9][0-9']*(?:[,'][0-9]{3})*\s*(?:PESOS|MXN)", s)
    if not m: return None
    num = re.sub(r"[^0-9]", "", m.group(0))
    return int(num)

def precio(num):
    return "${:,} MXN".format(num) if num else None
ACCENTS = {
    "agustin": "Agustín", "ajonjoli": "Ajonjolí", "alarcon": "Alarcón",
    "andalucia": "Andalucía", "cardenas": "Cárdenas", "chiquilistlan": "Chiquilistlán",
    "campina": "Campiña", "cristobal": "Cristóbal", "gonzalez": "González",
    "guevara": "Guevara", "jardin": "Jardín", "ladron": "Ladrón",
    "lazaro": "Lázaro", "americas": "Américas", "paraiso": "Paraíso", "yanez": "Yañez", "zuniga": "Zúñiga",
}

def slug_data(slug):
    base = re.sub(r"[A-Za-z0-9]{6,8}$", "", slug).rstrip("-")
    words = base.split("-")
    titulo = " ".join(ACCENTS.get(w, w.capitalize()) if (i == 0 or w not in SMALL) else w for i, w in enumerate(words))
    tipo = "Departamento" if "departamento" in slug else ("Terreno" if "terreno" in slug else ("Oficina" if "oficina" in slug else ("Bodega" if "bodega" in slug else "Casa")))
    oferta = oferta_de(slug)
    loc, key = DEFAULT_LOC
    for k, v in CITY_STATE.items():
        if k in slug:
            loc, key = v; break
    return titulo, tipo, oferta, loc, key

def descripcion(titulo, tipo, oferta, loc, texto):
    p = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", texto)).strip()
    if len(p) > 200: p = p[:200].rsplit(" ", 1)[0] + "…"
    return ("%s — %s en %s en %s. %s. Ofrecida por SADE Soluciones Inmobiliarias (SADE Inmobiliaria), agencia de bienes raíces con sede en Guadalajara y Zapopan, Jalisco, México. Para más información, fotos y visitas, contacta al +52 (333) 077-6110 o consulta el listado oficial en sadesi.com.mx." % (titulo, tipo.lower(), oferta.lower(), loc, p))

def escoger_img(html):
    m = re.search(r'property="og:image"\s+content="([^"]+)"', html)
    if m and LOGO_ID not in m.group(1): return m.group(1)
    for m in re.finditer(r'<img[^>]+src="(https://media\.wiggot\.mx/[^"]+)"', html):
        if LOGO_ID not in m.group(1): return m.group(1)
    return None

def schema_json(titulo, url, img, desc, precio_num, tipo):
    d = {
        "@context": "https://schema.org",
        "@type": "RealEstateListing",
        "name": titulo,
        "url": url,
        "image": img,
        "description": desc,
        "datePosted": "2026-08-18",
        "offers": {"@type": "Offer", "price": precio_num, "priceCurrency": "MXN", "availability": "https://schema.org/InStock"},
        "provider": {"@type": "RealEstateAgent", "name": "SADE Soluciones Inmobiliarias", "alternateName": "SADE Inmobiliaria", "url": "https://sadesi.com.mx/", "telephone": "+523330776110"},
    }
    return '<script type="application/ld+json">\n' + json.dumps(d, ensure_ascii=False, indent=2) + "\n</script>"
PAGE_TPL = """<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>@@TITLE@@ | SADE Inmobiliaria</title>
<meta name="description" content="@@DESC@@">
<link rel="canonical" href="@@URL@@">
<meta property="og:type" content="website">
<meta property="og:title" content="@@TITLE@@">
<meta property="og:description" content="@@DESC@@">
<meta property="og:url" content="@@URL@@">
<meta property="og:image" content="@@IMG@@">
<meta property="og:locale" content="es_MX">
<style>@@CSS@@</style>
@@SCHEMA@@
</head>
<body>
<header class="mini"><a href="../index.html"><img src="https://media.wiggot.mx/iy5iu5w-s.jpg" alt="SADE Soluciones Inmobiliarias"></a><a class="pill" href="tel:+523330776110">Tel +52 333 077 6110</a></header>
<main class="wrap">
<nav class="crumbs"><a href="../index.html">Inicio</a> › <a href="../propiedades.html">Propiedades</a></nav>
<div class="type">@@TIPO@@ en @@OFERTA@@</div>
<h1>@@TITULO@@</h1>
<p class="price">@@PRICE@@</p>
<img class="photo" src="@@IMG@@" alt="@@TITULO@@">
<div class="desc">@@DESC@@</div>
<div class="ctas">
<a class="cta" href="@@ORIGINAL@@" target="_blank" rel="noopener">Ver listado original en sadesi.com.mx</a>
<a class="cta" href="https://wa.me/523330776110?text=Hola%20SADE%2C%20me%20interesa%20%40%40TITULO%40%40" target="_blank" rel="noopener">WhatsApp</a>
<a class="cta ghost" href="tel:+523330776110">Llamar ahora</a>
</div>
</main>
<footer class="wrap">
<p>SADE Soluciones Inmobiliarias · Guadalajara y Zapopan, Jalisco, México</p>
<p><a href="mailto:contacto@sadesi.com.mx">contacto@sadesi.com.mx</a> · <a href="tel:+523330776110">+52 333 077 6110</a></p>
<p><a href="../sitemap.xml">Sitemap</a> · Listado oficial: <a href="https://sadesi.com.mx/propiedades" target="_blank" rel="noopener">sadesi.com.mx</a></p>
</footer>
</body>
</html>
"""

def page_html(d):
    html = PAGE_TPL
    for k, v in d.items():
        html = html.replace("@@%s@@" % k, v)
    return html
def fetch(url, tries=3):
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers=UA)
            return urllib.request.urlopen(req, timeout=25).read().decode("utf-8", "replace")
        except Exception as e:
            if i == tries - 1: raise
            time.sleep(1.5)
    return None

def main():
    smap = open("/tmp/smap.xml", encoding="utf-8").read() if os.path.exists("/tmp/smap.xml") else fetch("https://sadesi.com.mx/sitemap.xml")
    if not smap: raise SystemExit("No se pudo obtener el sitemap")
    urls = re.findall(r"<loc>(https://sadesi\.com\.mx/detalle-de-propiedad/[^<]+)</loc>", smap)
    print("URLs de propiedades:", len(urls))
    rows, errs = [], []
    for u in urls:
        slug = u.rstrip("/").rsplit("/", 1)[-1]
        raw_path = os.path.join("/tmp/prop_raw", slug + ".html")
        if os.path.exists(raw_path):
            html = open(raw_path, encoding="utf-8").read()
        else:
            try:
                html = fetch(u)
                open(raw_path, "w", encoding="utf-8").write(html)
                time.sleep(0.35)
            except Exception as e:
                errs.append((slug, str(e))); continue
        rows.append((slug, u, html))
    print("Filas listas:", len(rows), "| errores:", len(errs))
    if errs: print(errs[:5])
    return rows
def generar(rows):
    os.makedirs("propiedades", exist_ok=True)
    cards = []
    for slug, u, html in rows:
        titulo, tipo, oferta, loc, key = slug_data(slug)
        num = fmt_price(html)
        pr = precio(num)
        img = escoger_img(html) or "https://media.wiggot.mx/iy5iu5w-s.jpg"
        texto = re.sub(r"\s+", " ", re.sub(r"<script.*?</script>", " ", html, flags=re.S))[:600]
        desc = descripcion(titulo, tipo, oferta, loc, texto)
        url = "%s/propiedades/%s.html" % (SITE, slug)
        schema = schema_json(titulo, url, img, desc, num, tipo)
        d = {"TITLE": titulo, "DESC": desc, "URL": url, "IMG": img,
             "TIPO": tipo, "OFERTA": oferta, "PRICE": pr or "Precio disponible", "ORIGINAL": u,
             "SCHEMA": schema, "CSS": CSS}
        open("propiedades/%s.html" % slug, "w", encoding="utf-8").write(page_html(d))
        cards.append((slug, titulo, tipo, oferta, loc, key, pr, img))
    return cards
def catalog(cards):
    intro = """<div class="intro"><h2>Casas, departamentos, terrenos, oficinas y bodegas en Guadalajara y Zapopan</h2>
<p>En SADE Soluciones Inmobiliarias (SADE Inmobiliaria) encontrará casas en venta en Guadalajara y Zapopan, departamentos en renta y en venta, terrenos en venta en Tlajomulco, oficinas en renta en Puerta de Hierro y bodegas industriales en Jalisco. Con más de 14 años de experiencia, lo acompañamos en la compra, venta o renta de su inmueble en la Zona Metropolitana de Guadalajara. Consulte el catálogo y contacte al +52 (333) 077-6110 o visite el listado oficial en sadesi.com.mx.</p></div>"""
    def card(slug, titulo, tipo, oferta, loc, key, pr, img):
        return """<a class="card" href="propiedades/%s.html"><img src="%s" alt="%s en %s en %s" loading="lazy">
<div class="card-body"><span class="badge">%s</span><h2>%s</h2><p class="p2">%s</p><p class="loc">%s</p></div></a>""" % (slug, img, tipo, oferta, key, oferta, titulo, pr or "Consultar precio", loc)
    body = "".join(card(*c) for c in cards)
    return intro, body

def sitemap_txt(cards):
    lastmod = "2026-08-18"
    lines = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for url, lm in [(SITE + "/", lastmod), (SITE + "/propiedades.html", lastmod)]:
        lines.append("<url><loc>%s</loc><lastmod>%s</lastmod></url>" % (url, lm))
    for slug, *_ in cards:
        lines.append("<url><loc>%s/propiedades/%s.html</loc><lastmod>%s</lastmod></url>" % (SITE, slug, lastmod))
    lines.append("</urlset>")
    return "\n".join(lines) + "\n"
CAT_TPL = """<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Propiedades en venta y renta en Guadalajara y Zapopan | SADE Inmobiliaria</title>
<meta name="description" content="Catálogo de casas en venta en Guadalajara y Zapopan, departamentos en renta y en venta, terrenos en venta en Tlajomulco, oficinas en renta y bodegas industriales. SADE Soluciones Inmobiliarias, más de 14 años de experiencia.">
<link rel="canonical" href="@@URL@@">
<meta property="og:type" content="website">
<meta property="og:title" content="Propiedades en venta y renta en Guadalajara y Zapopan | SADE Inmobiliaria">
<meta property="og:url" content="@@URL@@">
<meta property="og:locale" content="es_MX">
<style>@@CSS@@</style>
<script type="application/ld+json">
{"@context":"https://schema.org","@type":"RealEstateAgent","name":"SADE Soluciones Inmobiliarias","alternateName":"SADE Inmobiliaria","url":"https://sadesi.com.mx/","telephone":"+523330776110","areaServed":["Guadalajara","Zapopan","Tlajomulco de Zúñiga","Jalisco"],"address":{"@type":"PostalAddress","addressRegion":"Jalisco","addressCountry":"MX"}}
</script>
</head>
<body>
<header class="mini"><a href="index.html"><img src="https://media.wiggot.mx/iy5iu5w-s.jpg" alt="SADE Soluciones Inmobiliarias"></a><a class="pill" href="tel:+523330776110">Tel +52 333 077 6110</a></header>
<main class="wrap">
<nav class="crumbs"><a href="index.html">Inicio</a></nav>
<h1>Propiedades en venta y renta en Guadalajara y Zapopan</h1>
@@INTRO@@
<div class="grid">@@CARDS@@</div>
</main>
<footer class="wrap">
<p>SADE Soluciones Inmobiliarias · Guadalajara y Zapopan, Jalisco, México</p>
<p><a href="mailto:contacto@sadesi.com.mx">contacto@sadesi.com.mx</a> · <a href="tel:+523330776110">+52 333 077 6110</a></p>
<p><a href="sitemap.xml">Sitemap</a> · Listado oficial: <a href="https://sadesi.com.mx/propiedades" target="_blank" rel="noopener">sadesi.com.mx</a></p>
</footer>
</body>
</html>
"""

def build_all():
    rows = main()
    cards = generar(rows)
    intro, body = catalog(cards)
    cat = CAT_TPL.replace("@@URL@@", SITE + "/propiedades.html").replace("@@CSS@@", CSS).replace("@@INTRO@@", intro).replace("@@CARDS@@", body)
    open("propiedades.html", "w", encoding="utf-8").write(cat)
    open("sitemap.xml", "w", encoding="utf-8").write(sitemap_txt(cards))
    idx = open("index.html", encoding="utf-8").read()
    if "https://sadesi.com.mx/propiedades" in idx:
        idx = idx.replace('href="https://sadesi.com.mx/propiedades"', 'href="propiedades.html"')
        open("index.html", "w", encoding="utf-8").write(idx)
        print("index.html: enlace a propiedades actualizado")
    print("Páginas generadas:", len(cards), "| sitemap URLs:", len(cards) + 2)

if __name__ == "__main__":
    build_all()
