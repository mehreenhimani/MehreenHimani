"""Save a .fodt as .odt with fonts embedded, plus a PDF preview.

Usage: python3 save_odt.py in.fodt out.odt [font.ttf ...]
Needs a running soffice listening on port 2002, e.g.:
    soffice --headless --norestore --accept="socket,host=localhost,port=2002;urp;" &
"""
import sys
import time
import uno
from com.sun.star.beans import PropertyValue


def prop(name, value):
    p = PropertyValue()
    p.Name, p.Value = name, value
    return p


src, dst = (uno.systemPathToFileUrl(p) for p in sys.argv[1:3])
local = uno.getComponentContext()
resolver = local.ServiceManager.createInstanceWithContext("com.sun.star.bridge.UnoUrlResolver", local)
for _ in range(60):
    try:
        ctx = resolver.resolve("uno:socket,host=localhost,port=2002;urp;StarOffice.ComponentContext")
        break
    except Exception:
        time.sleep(1)
desktop = ctx.ServiceManager.createInstanceWithContext("com.sun.star.frame.Desktop", ctx)
doc = desktop.loadComponentFromURL(src, "_blank", 0, (prop("Hidden", True),))
settings = doc.createInstance("com.sun.star.document.Settings")
settings.EmbedFonts = True
settings.EmbedOnlyUsedFonts = True
settings.EmbedLatinScriptFonts = True
doc.storeToURL(dst, (prop("FilterName", "writer8"),))
doc.close(True)
print("saved", sys.argv[2])


def embed_fonts(odt, ttf_files, family="Latin Modern Roman"):
    """Pack TrueType files into the .odt and reference them from the font-face declaration."""
    import os
    import re
    import zipfile
    zin = zipfile.ZipFile(odt)
    files = {n: zin.read(n) for n in zin.namelist()}
    zin.close()
    uris = "".join(
        f'<svg:font-face-uri xlink:href="Fonts/{os.path.basename(f)}" xlink:type="simple">'
        f'<svg:font-face-format svg:string="truetype"/></svg:font-face-uri>' for f in ttf_files)
    pat = re.compile(r'<style:font-face style:name="%s"([^>]*?)/>' % re.escape(family))
    for part in ("content.xml", "styles.xml"):
        xml = files[part].decode()
        xml = pat.sub(lambda m: f'<style:font-face style:name="{family}"{m.group(1)}>'
                                f'<svg:font-face-src>{uris}</svg:font-face-src></style:font-face>', xml)
        files[part] = xml.encode()
    manifest = files["META-INF/manifest.xml"].decode()
    entries = "".join(f' <manifest:file-entry manifest:full-path="Fonts/{os.path.basename(f)}" '
                      f'manifest:media-type="application/x-font-ttf"/>\n' for f in ttf_files)
    files["META-INF/manifest.xml"] = manifest.replace("</manifest:manifest>", entries + "</manifest:manifest>").encode()
    for f in ttf_files:
        files["Fonts/" + os.path.basename(f)] = open(f, "rb").read()
    with zipfile.ZipFile(odt, "w") as z:
        z.writestr(zipfile.ZipInfo("mimetype"), files.pop("mimetype"), compress_type=zipfile.ZIP_STORED)
        for n, data in files.items():
            z.writestr(n, data, compress_type=zipfile.ZIP_DEFLATED)


if len(sys.argv) > 3:
    embed_fonts(sys.argv[2], sys.argv[3:])
    print("embedded", len(sys.argv) - 3, "font files")
