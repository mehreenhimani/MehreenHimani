"""Build an OpenDocument (.fodt) version of the CV from the LaTeX source.

Mirrors the LaTeX layout: centred header, ruled section headings, bold role
lines with right-aligned dates, italic headline lines, and bullet lists.
Convert the result to .odt with:
    soffice --headless --convert-to odt <file>.fodt
"""
import re
import sys
from xml.sax.saxutils import escape

SRC = sys.argv[1]
OUT = sys.argv[2]
tex = open(SRC, encoding="utf-8").read()
body = tex.split(r"\begin{document}", 1)[1].split(r"\end{document}", 1)[0]
# Drop comments (unescaped %) but keep \%
body = re.sub(r"(?<!\\)%.*", "", body)

FONT = "Latin Modern Roman"


def read_group(s, i):
    """Return (content, index after closing brace) for a {...} group at s[i]."""
    while s[i].isspace():
        i += 1
    assert s[i] == "{", s[i:i + 40]
    depth, j = 0, i
    while True:
        c = s[j]
        if c == "\\":
            j += 2
            continue
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return s[i + 1:j], j + 1
        j += 1


SIMPLE = [
    ("~", " "), (r"\,|\,", " | "), (r"$\cdot$", "·"), (r"$\rightarrow$", "→"),
    (r"\textasciitilde", "~"), (r"\textregistered", "®"),
    ("---", "—"), ("--", "–"), ("``", "“"), ("''", "”"),
    (r"\&", "&"), (r"\%", "%"), (r"\$", "$"), (r"\,", " "),
]


def inline(s, style=None):
    """Convert inline TeX to ODF text:span / text:a markup."""
    out, i = [], 0
    buf = []

    def flush():
        if buf:
            t = "".join(buf)
            for a, b in SIMPLE:
                t = t.replace(a, b)
            t = re.sub(r"\s+", " ", t)
            t = escape(t)
            out.append(f'<text:span text:style-name="{style}">{t}</text:span>' if style else t)
            buf.clear()

    while i < len(s):
        m = re.match(r"\\(textbf|textit|mbox|textsuperscript|href)\{", s[i:])
        if m:
            flush()
            cmd = m.group(1)
            content, i = read_group(s, i + len(cmd) + 1)
            if cmd == "href":
                text, i = read_group(s, i)
                out.append(f'<text:a text:style-name="Internet_20_link" text:visited-style-name="Internet_20_link" xlink:type="simple" xlink:href="{escape(content)}">'
                           f'{inline(text, style)}</text:a>')
            elif cmd == "mbox":
                out.append(f'<text:span text:style-name="NoHyph">{inline(content, style)}</text:span>')
            else:
                new = {"textbf": "B", "textit": "I", "textsuperscript": "Sup"}.get(cmd, style)
                if style == "B" and new == "I":
                    new = "BI"
                out.append(inline(content, new))
            continue
        buf.append(s[i])
        i += 1
    flush()
    return "".join(out)


def para(style, content):
    return f'<text:p text:style-name="{style}">{content}</text:p>'


def row(style, left, right, table):
    """Borderless two-column table: wrapping text left, date right-aligned."""
    return (f'<table:table table:style-name="{table}">'
            f'<table:table-column table:style-name="{table}.A"/><table:table-column table:style-name="{table}.B"/>'
            f'<table:table-row><table:table-cell table:style-name="Cell" office:value-type="string">{para(style, left)}</table:table-cell>'
            f'<table:table-cell table:style-name="Cell" office:value-type="string">{para("Date", right)}</table:table-cell>'
            f'</table:table-row></table:table>')


xml = []

# ---- Header ----
hdr = re.search(r"\\begin\{center\}(.*?)\\end\{center\}", body, re.S).group(1)
lines = [l.strip() for l in re.split(r"\\\\(?:\[[^\]]*\])?", hdr) if l.strip()]
name = re.search(r"\\bfseries\s+(.*)\}", lines[0]).group(1)
xml.append(para("Name", escape(name)))
for l in lines[1:]:
    xml.append(para("Contact", inline(l.replace("\n", " "))))
body = body[body.index(r"\end{center}") + len(r"\end{center}"):]

# ---- Sections ----
for sec in re.split(r"\\section\*", body)[1:]:
    title, end = read_group(sec, 0)
    rest = sec[end:]
    xml.append(para("Section", inline(title)))
    i = 0
    rest = rest.strip()
    if not re.search(r"\\(role|project|begin)", rest):
        xml.append(para("Summary", inline(rest)))
        continue
    while i < len(rest):
        m = re.match(r"\s*\\(role|project)\{", rest[i:])
        if m:
            i += m.end() - 1
            left, i = read_group(rest, i)
            date, i = read_group(rest, i)
            sub, i = read_group(rest, i)
            xml.append(row("Entry", inline(left), inline(date), "Role"))
            xml.append(para("Headline", inline(sub, "I")))
            continue
        m = re.match(r"\s*\\begin\{itemize\}(\[[^\]]*\])?(.*?)\\end\{itemize\}", rest[i:], re.S)
        if m:
            plain = bool(m.group(1))
            items = [x.strip() for x in m.group(2).split(r"\item") if x.strip()]
            if plain:
                xml += [para("SkillLine", inline(it)) for it in items]
            else:
                xml.append('<text:list text:style-name="Bullets">')
                xml += [f"<text:list-item>{para('Bullet', inline(it))}</text:list-item>" for it in items]
                xml.append("</text:list>")
            i += m.end()
            continue
        m = re.match(r"\s*\\begin\{tabularx\}", rest[i:])
        if m:
            j = i + m.end()
            _, j = read_group(rest, j)
            _, j = read_group(rest, j)
            k = rest.index(r"\end{tabularx}", j)
            rows = [r.strip() for r in re.split(r"\\\\(?:\[[^\]]*\])?", rest[j:k]) if r.strip()]
            for r in rows:
                left, right = r.rsplit("&", 1)
                xml.append(row("TableLine", inline(left), inline(right), "Edu"))
            i = k + len(r"\end{tabularx}")
            continue
        m = re.match(r"\s*\\entrygap\s*", rest[i:])
        if m:
            xml.append(para("Gap", ""))
            i += m.end()
            continue
        if rest[i:].strip() == "" or re.match(r"\s*\\vspace\{[^}]*\}", rest[i:]):
            m = re.match(r"\s*(\\vspace\{[^}]*\})?", rest[i:])
            i += max(m.end(), 1)
            continue
        raise SystemExit(f"Unparsed: {rest[i:i + 80]!r}")

# Letter paper, 0.7in side margins, 0.6in top/bottom — same as the LaTeX
TAB = "7.1in"
doc = f"""<?xml version="1.0" encoding="UTF-8"?>
<office:document xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0"
 xmlns:style="urn:oasis:names:tc:opendocument:xmlns:style:1.0"
 xmlns:text="urn:oasis:names:tc:opendocument:xmlns:text:1.0"
 xmlns:fo="urn:oasis:names:tc:opendocument:xmlns:xsl-fo-compatible:1.0"
 xmlns:svg="urn:oasis:names:tc:opendocument:xmlns:svg-compatible:1.0"
 xmlns:xlink="http://www.w3.org/1999/xlink"
 xmlns:dc="http://purl.org/dc/elements/1.1/"
 xmlns:meta="urn:oasis:names:tc:opendocument:xmlns:meta:1.0"
 xmlns:table="urn:oasis:names:tc:opendocument:xmlns:table:1.0"
 xmlns:config="urn:oasis:names:tc:opendocument:xmlns:config:1.0"
 office:version="1.3" office:mimetype="application/vnd.oasis.opendocument.text">
<office:meta><dc:title>Mehreen Himani — CV</dc:title><meta:initial-creator>Mehreen Himani</meta:initial-creator></office:meta>
<office:settings><config:config-item-set config:name="ooo:configuration-settings">
 <config:config-item config:name="EmbedFonts" config:type="boolean">true</config:config-item>
 <config:config-item config:name="EmbedOnlyUsedFonts" config:type="boolean">true</config:config-item>
</config:config-item-set></office:settings>
<office:font-face-decls>
 <style:font-face style:name="{FONT}" svg:font-family="'{FONT}'" style:font-family-generic="roman"/>
</office:font-face-decls>
<office:styles>
 <style:default-style style:family="paragraph">
  <style:paragraph-properties fo:hyphenation-ladder-count="no-limit"/>
  <style:text-properties style:font-name="{FONT}" style:font-name-asian="{FONT}" style:font-name-complex="{FONT}" fo:font-size="10pt" fo:language="en" fo:country="GB" fo:hyphenate="true" fo:hyphenation-remain-char-count="3" fo:hyphenation-push-char-count="3"/>
 </style:default-style>
 <style:style style:name="Standard" style:family="paragraph">
  <style:paragraph-properties fo:margin-top="0in" fo:margin-bottom="0in" fo:line-height="12pt"/>
 </style:style>
 <style:style style:name="Name" style:family="paragraph" style:parent-style-name="Standard">
  <style:paragraph-properties fo:text-align="center" fo:margin-bottom="0.07in" fo:line-height="30pt"/>
  <style:text-properties fo:font-size="23pt" fo:font-weight="bold"/>
 </style:style>
 <style:style style:name="Contact" style:family="paragraph" style:parent-style-name="Standard">
  <style:paragraph-properties fo:text-align="center" fo:margin-bottom="0.04in"/>
 </style:style>
 <style:style style:name="Section" style:family="paragraph" style:parent-style-name="Standard">
  <style:paragraph-properties fo:margin-top="0.12in" fo:margin-bottom="0.06in" fo:padding-bottom="0.02in"
    fo:border-bottom="0.5pt solid #000000" fo:border-top="none" fo:border-left="none" fo:border-right="none" fo:keep-with-next="always" fo:line-height="15pt"/>
  <style:text-properties fo:font-size="12.5pt" fo:font-weight="bold"/>
 </style:style>
 <style:style style:name="Summary" style:family="paragraph" style:parent-style-name="Standard">
  <style:paragraph-properties fo:text-align="justify"/>
 </style:style>
 <style:style style:name="Entry" style:family="paragraph" style:parent-style-name="Standard">
  <style:paragraph-properties fo:keep-with-next="always">
   <style:tab-stops><style:tab-stop style:position="{TAB}" style:type="right"/></style:tab-stops>
  </style:paragraph-properties>
 </style:style>
 <style:style style:name="Headline" style:family="paragraph" style:parent-style-name="Standard">
  <style:paragraph-properties fo:keep-with-next="always" fo:margin-bottom="0.02in"/>
 </style:style>
 <style:style style:name="Bullet" style:family="paragraph" style:parent-style-name="Standard">
  <style:paragraph-properties fo:text-align="justify" fo:margin-bottom="0.015in"/>
 </style:style>
 <style:style style:name="Gap" style:family="paragraph" style:parent-style-name="Standard">
  <style:text-properties fo:font-size="4pt"/>
 </style:style>
 <style:style style:name="SkillLine" style:family="paragraph" style:parent-style-name="Standard">
  <style:paragraph-properties fo:margin-left="0.08in" fo:margin-bottom="0.03in" fo:text-align="justify"/>
 </style:style>
 <style:style style:name="TableLine" style:family="paragraph" style:parent-style-name="Standard">
  <style:paragraph-properties fo:margin-left="0.08in" fo:margin-bottom="0.03in">
   <style:tab-stops><style:tab-stop style:position="{TAB.replace('7.1', '7.02')}" style:type="right"/></style:tab-stops>
  </style:paragraph-properties>
 </style:style>
 <style:style style:name="Date" style:family="paragraph" style:parent-style-name="Standard">
  <style:paragraph-properties fo:text-align="end"/>
 </style:style>
 <style:style style:name="Internet_20_link" style:display-name="Internet link" style:family="text">
  <style:text-properties fo:color="#000000" style:text-underline-style="none"/>
 </style:style>
 <style:style style:name="NoHyph" style:family="text"><style:text-properties fo:hyphenate="false"/></style:style>
 <style:style style:name="B" style:family="text"><style:text-properties fo:font-weight="bold"/></style:style>
 <style:style style:name="I" style:family="text"><style:text-properties fo:font-style="italic"/></style:style>
 <style:style style:name="BI" style:family="text"><style:text-properties fo:font-weight="bold" fo:font-style="italic"/></style:style>
 <style:style style:name="Sup" style:family="text"><style:text-properties style:text-position="super 58%" fo:font-weight="bold"/></style:style>
 <text:list-style style:name="Bullets">
  <text:list-level-style-bullet text:level="1" text:bullet-char="•">
   <style:list-level-properties text:list-level-position-and-space-mode="label-alignment">
    <style:list-level-label-alignment text:label-followed-by="listtab" text:list-tab-stop-position="0.3in"
      fo:text-indent="-0.14in" fo:margin-left="0.3in"/>
   </style:list-level-properties>
  </text:list-level-style-bullet>
 </text:list-style>
</office:styles>
<office:automatic-styles>
 <style:style style:name="Role" style:family="table"><style:table-properties style:width="7.1in" table:align="margins" fo:margin-top="0in" fo:margin-bottom="0in" style:may-break-between-rows="false" fo:keep-with-next="always"/></style:style>
 <style:style style:name="Role.A" style:family="table-column"><style:table-column-properties style:column-width="5.75in"/></style:style>
 <style:style style:name="Role.B" style:family="table-column"><style:table-column-properties style:column-width="1.35in"/></style:style>
 <style:style style:name="Edu" style:family="table"><style:table-properties style:width="7.02in" fo:margin-left="0.08in" table:align="left" fo:margin-bottom="0.03in"/></style:style>
 <style:style style:name="Edu.A" style:family="table-column"><style:table-column-properties style:column-width="5.9in"/></style:style>
 <style:style style:name="Edu.B" style:family="table-column"><style:table-column-properties style:column-width="1.12in"/></style:style>
 <style:style style:name="Cell" style:family="table-cell"><style:table-cell-properties fo:padding="0in" fo:border="none" style:vertical-align="top"/></style:style>
 <style:page-layout style:name="PL">
  <style:page-layout-properties fo:page-width="8.5in" fo:page-height="11in"
    fo:margin-left="0.7in" fo:margin-right="0.7in" fo:margin-top="0.6in" fo:margin-bottom="0.6in"/>
 </style:page-layout>
</office:automatic-styles>
<office:master-styles><style:master-page style:name="Standard" style:page-layout-name="PL"/></office:master-styles>
<office:body><office:text>
{chr(10).join(xml)}
</office:text></office:body></office:document>
"""
open(OUT, "w", encoding="utf-8").write(doc)
print(f"wrote {OUT}: {len(xml)} blocks")
