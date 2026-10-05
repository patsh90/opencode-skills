#!/usr/bin/env python3
"""Regenerate ../reference.odt, the style template used by pandoc.

All styling for the letters lives in this template: page sizes and margins,
fonts, body/heading/address/signature paragraph styles, the frame style used
for the window-envelope address blocks, and the page styles that put page
numbers on page 2 onward.

Usage:  python3 make_reference.py [output.odt]

You can also open reference.odt in LibreOffice, edit the styles (F11), and
save it as ODT. md2odt.py only patches the handful of attributes that the
frontmatter may override (paper, margins, font, size, spacing, alignment),
so manual edits to everything else are kept.
"""
import sys
import zipfile
from pathlib import Path

NS = (
    'xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0" '
    'xmlns:style="urn:oasis:names:tc:opendocument:xmlns:style:1.0" '
    'xmlns:text="urn:oasis:names:tc:opendocument:xmlns:text:1.0" '
    'xmlns:table="urn:oasis:names:tc:opendocument:xmlns:table:1.0" '
    'xmlns:draw="urn:oasis:names:tc:opendocument:xmlns:drawing:1.0" '
    'xmlns:fo="urn:oasis:names:tc:opendocument:xmlns:xsl-fo-compatible:1.0" '
    'xmlns:xlink="http://www.w3.org/1999/xlink" '
    'xmlns:dc="http://purl.org/dc/elements/1.1/" '
    'xmlns:meta="urn:oasis:names:tc:opendocument:xmlns:meta:1.0" '
    'xmlns:number="urn:oasis:names:tc:opendocument:xmlns:datastyle:1.0" '
    'xmlns:svg="urn:oasis:names:tc:opendocument:xmlns:svg-compatible:1.0" '
    'xmlns:loext="urn:org:documentfoundation:names:experimental:office:xmlns:loext:1.0" '
    'office:version="1.3"'
)

# ---- defaults (A4 only, 25 mm margins, Liberation Serif 12 pt, 1.15 spacing) ----
PAGE_W, PAGE_H, MARGIN = "210mm", "297mm", "25mm"
FONT, SIZE, LINE, ALIGN = "Liberation Serif", "12pt", "115%", "start"


def pstyle(name, display, parent="Standard", nxt=None, para="", txt="",
           cls="text", extra=""):
    nxt_attr = f' style:next-style-name="{nxt}"' if nxt else ""
    p = f"<style:paragraph-properties {para}/>" if para else ""
    t = f"<style:text-properties {txt}/>" if txt else ""
    return (f'<style:style style:name="{name}" style:display-name="{display}" '
            f'style:family="paragraph" style:parent-style-name="{parent}"'
            f'{nxt_attr} style:class="{cls}"{extra}>{p}{t}</style:style>')


KEEP = 'fo:keep-with-next="always" fo:keep-together="always"'
NOHYPH = 'fo:hyphenate="false"'

styles = [
    # Standard: single spacing base for address blocks, tables, footer.
    f'<style:style style:name="Standard" style:family="paragraph" style:class="text">'
    f'<style:paragraph-properties fo:margin-top="0mm" fo:margin-bottom="0mm" '
    f'fo:orphans="2" fo:widows="2"/></style:style>',

    # ---- body ----
    pstyle("Text_20_body", "Text Body",
           para=f'fo:margin-top="0mm" fo:margin-bottom="3.5mm" '
                f'fo:line-height="{LINE}" fo:text-align="{ALIGN}" '
                f'style:justify-single-word="false" fo:orphans="2" fo:widows="2"',
           txt='fo:hyphenate="false" fo:hyphenation-remain-char-count="3" '
               'fo:hyphenation-push-char-count="3"'),
    pstyle("First_20_paragraph", "First Paragraph", parent="Text_20_body",
           nxt="Text_20_body"),
    pstyle("List", "List", parent="Text_20_body", cls="list"),
    pstyle("Quotations", "Quotations", parent="Text_20_body",
           para='fo:margin-left="10mm" fo:margin-right="10mm"'),
    pstyle("Table_20_Contents", "Table Contents", cls="extra",
           para='fo:margin-top="0.8mm" fo:margin-bottom="0.8mm"'),
    pstyle("Table_20_Heading", "Table Heading", parent="Table_20_Contents",
           cls="extra", txt='fo:font-weight="bold"'),
    pstyle("Table", "Table", parent="Standard", cls="extra"),
    pstyle("Caption", "Caption", cls="extra",
           para='fo:margin-top="1.5mm" fo:margin-bottom="1.5mm"',
           txt='fo:font-size="90%" fo:font-style="italic"'),
    pstyle("Footnote", "Footnote", cls="extra",
           para='fo:margin-left="4mm" fo:text-indent="-4mm"',
           txt='fo:font-size="83%"'),
    pstyle("Header", "Header", cls="extra"),
    pstyle("Footer", "Footer", cls="extra",
           para='fo:text-align="center"', txt='fo:font-size="83%"'),
    pstyle("Horizontal_20_Line", "Horizontal Line", cls="html",
           para='fo:margin-bottom="3mm" fo:border-bottom="0.5pt solid #000000" '
                'fo:padding="0mm"', txt='fo:font-size="6pt"'),

    # ---- headings: never orphaned (keep-with-next) ----
    pstyle("Heading", "Heading", nxt="Text_20_body",
           para=f'fo:margin-top="5mm" fo:margin-bottom="2mm" {KEEP}',
           txt=f'fo:font-weight="bold" {NOHYPH}'),
    pstyle("Heading_20_1", "Heading 1", parent="Heading", nxt="Text_20_body",
           txt='fo:font-size="117%"', extra=' style:default-outline-level="1"'),
    pstyle("Heading_20_2", "Heading 2", parent="Heading", nxt="Text_20_body",
           txt='fo:font-size="100%"', extra=' style:default-outline-level="2"'),
    pstyle("Heading_20_3", "Heading 3", parent="Heading", nxt="Text_20_body",
           txt='fo:font-size="100%" fo:font-style="italic"',
           extra=' style:default-outline-level="3"'),
    pstyle("Heading_20_4", "Heading 4", parent="Heading", nxt="Text_20_body",
           txt='fo:font-size="100%" fo:font-weight="normal" fo:font-style="italic"',
           extra=' style:default-outline-level="4"'),
    pstyle("Title", "Title", parent="Heading", nxt="Subtitle", cls="chapter",
           para='fo:text-align="center" fo:margin-top="0mm" fo:margin-bottom="3mm"',
           txt='fo:font-size="150%"'),
    pstyle("Subtitle", "Subtitle", parent="Heading", nxt="Text_20_body",
           cls="chapter", para='fo:text-align="center" fo:margin-top="0mm"',
           txt='fo:font-size="117%" fo:font-weight="normal"'),
    pstyle("Author", "Author", parent="Standard", cls="chapter",
           para='fo:text-align="center" fo:margin-bottom="2mm"'),
    pstyle("Date", "Date", parent="Standard", cls="chapter",
           para='fo:text-align="center" fo:margin-bottom="8mm"'),
    pstyle("Abstract", "Abstract", parent="Text_20_body", cls="chapter"),

    # ---- letter parts (used by letter.lua) ----
    # Empty first paragraph that switches page 1 to the "First Page" style.
    pstyle("Document_20_Start", "Document Start",
           para='fo:line-height="100%"', txt='fo:font-size="2pt"',
           extra=' style:master-page-name="First_20_Page"'),
    # Address blocks sit in frames: single spacing, never split.
    pstyle("Letter_20_Sender", "Letter Sender",
           para=f'fo:text-align="end" fo:line-height="100%" {KEEP}',
           txt=NOHYPH),
    # used when window_side: right puts the sender in the left column
    pstyle("Letter_20_Sender_20_Left", "Letter Sender Left", parent="Letter_20_Sender",
           para='fo:text-align="start"'),
    pstyle("Letter_20_Return_20_Line", "Letter Return Line",
           para=f'fo:line-height="100%" {KEEP}',
           txt=f'fo:font-size="65%" style:text-underline-style="solid" '
               f'style:text-underline-width="auto" style:text-underline-color="font-color" {NOHYPH}'),
    pstyle("Letter_20_Recipient", "Letter Recipient",
           para=f'fo:line-height="100%" {KEEP}', txt=NOHYPH),
    pstyle("Letter_20_Date", "Letter Date",
           para='fo:text-align="end" fo:margin-top="8mm" fo:margin-bottom="5mm" '
                'fo:keep-with-next="always"', txt=NOHYPH),
    # Polish layout: "Place, date" in a frame at the top right
    pstyle("Letter_20_Date_20_Top", "Letter Date Top",
           para=f'fo:text-align="end" fo:line-height="100%" {KEEP}', txt=NOHYPH),
    # space after the address field when the date is at the top
    pstyle("Letter_20_Address_20_Gap", "Letter Address Gap",
           para='fo:margin-top="0mm" fo:margin-bottom="8mm" fo:line-height="100%"',
           txt='fo:font-size="2pt"'),
    pstyle("Letter_20_Reference", "Letter Reference",
           para='fo:margin-bottom="2mm" fo:keep-with-next="always"', txt=NOHYPH),
    pstyle("Letter_20_Subject", "Letter Subject",
           para=f'fo:margin-top="0mm" fo:margin-bottom="6mm" {KEEP}',
           txt=f'fo:font-weight="bold" {NOHYPH}'),
    pstyle("Letter_20_Salutation", "Letter Salutation", parent="Text_20_body",
           para='fo:keep-with-next="always"'),
    pstyle("Letter_20_Closing", "Letter Closing", parent="Text_20_body",
           para=f'fo:margin-top="3mm" fo:margin-bottom="0mm" {KEEP}',
           txt=NOHYPH),
    # ~3 blank lines of signature space above the typed name.
    pstyle("Letter_20_Signature", "Letter Signature",
           para=f'fo:margin-top="15mm" fo:margin-bottom="0mm" fo:line-height="100%" '
                f'fo:text-align="start" {KEEP}', txt=NOHYPH),
    pstyle("Letter_20_Signature_20_Title", "Letter Signature Title",
           parent="Letter_20_Signature",
           para='fo:margin-top="0mm"'),
    # sign-off in the right half of the text area (Polish convention)
    pstyle("Letter_20_Closing_20_Right", "Letter Closing Right", parent="Letter_20_Closing",
           para='fo:margin-left="80mm" fo:text-align="center"'),
    pstyle("Letter_20_Signature_20_Right", "Letter Signature Right", parent="Letter_20_Signature",
           para='fo:margin-left="80mm" fo:text-align="center"'),
    pstyle("Letter_20_Signature_20_Title_20_Right", "Letter Signature Title Right",
           parent="Letter_20_Signature_20_Title",
           para='fo:margin-left="80mm" fo:text-align="center"'),
    pstyle("Letter_20_Spacer", "Letter Spacer",
           para='fo:margin-top="0mm" fo:margin-bottom="2.5mm" fo:line-height="100%"',
           txt='fo:font-size="2pt"'),
    pstyle("Letter_20_Enclosures", "Letter Enclosures",
           para='fo:margin-top="8mm" fo:line-height="100%" fo:keep-together="always"',
           txt=NOHYPH),

    # ---- character styles pandoc may reference ----
    '<style:style style:name="Emphasis" style:family="text"><style:text-properties fo:font-style="italic"/></style:style>',
    '<style:style style:name="Strong_20_Emphasis" style:display-name="Strong Emphasis" style:family="text"><style:text-properties fo:font-weight="bold"/></style:style>',
    '<style:style style:name="Source_20_Text" style:display-name="Source Text" style:family="text"><style:text-properties style:font-name="Liberation Mono" fo:font-size="90%"/></style:style>',
    '<style:style style:name="Internet_20_link" style:display-name="Internet link" style:family="text"><style:text-properties fo:color="#000000" style:text-underline-style="none"/></style:style>',
    '<style:style style:name="Footnote_20_anchor" style:display-name="Footnote anchor" style:family="text"><style:text-properties style:text-position="super 58%"/></style:style>',
    '<style:style style:name="Footnote_20_Symbol" style:display-name="Footnote Symbol" style:family="text"/>',
    '<style:style style:name="Bullet_20_Symbols" style:display-name="Bullet Symbols" style:family="text"/>',
    '<style:style style:name="Numbering_20_Symbols" style:display-name="Numbering Symbols" style:family="text"/>',

    # Frame style for sender / return line / recipient blocks.
    # wrap=none: body text never runs beside a frame, so the flow starts
    # below the address field whatever the paper size.
    '<style:style style:name="Letter_20_Frame" style:display-name="Letter Frame" style:family="graphic">'
    '<style:graphic-properties style:wrap="none" style:number-wrapped-paragraphs="no-limit" '
    'style:vertical-pos="from-top" style:vertical-rel="page" '
    'style:horizontal-pos="from-left" style:horizontal-rel="page" '
    'fo:margin-left="0mm" fo:margin-right="0mm" fo:margin-top="0mm" fo:margin-bottom="0mm" '
    'fo:padding="0mm" fo:border="none" draw:fill="none" fo:background-color="transparent" '
    'style:background-transparency="100%" style:flow-with-text="false" style:protect="position size"/>'
    '</style:style>',
    '<style:style style:name="Letter_20_Mark" style:display-name="Letter Mark" style:family="graphic">'
    '<style:graphic-properties style:wrap="run-through" style:run-through="foreground" '
    'style:vertical-pos="from-top" style:vertical-rel="page" '
    'style:horizontal-pos="from-left" style:horizontal-rel="page" '
    'fo:padding="0mm" fo:border="none" fo:border-top="0.2mm solid #000000" '
    'draw:fill="none" fo:background-color="transparent" style:flow-with-text="false"/>'
    '</style:style>',
]

STYLES_XML = f"""<?xml version="1.0" encoding="UTF-8"?>
<office:document-styles {NS}>
<office:font-face-decls>
<style:font-face style:name="{FONT}" svg:font-family="'{FONT}'" style:font-family-generic="roman" style:font-pitch="variable"/>
<style:font-face style:name="Liberation Mono" svg:font-family="'Liberation Mono'" style:font-family-generic="modern" style:font-pitch="fixed"/>
</office:font-face-decls>
<office:styles>
<style:default-style style:family="paragraph">
<style:paragraph-properties fo:orphans="2" fo:widows="2" style:writing-mode="page" style:tab-stop-distance="12.5mm"/>
<style:text-properties style:font-name="{FONT}" fo:font-size="{SIZE}" fo:language="en" fo:country="GB" fo:hyphenate="false" style:use-window-font-color="true"/>
</style:default-style>
<style:default-style style:family="table"><style:table-properties table:border-model="collapsing"/></style:default-style>
<style:default-style style:family="graphic"><style:graphic-properties style:flow-with-text="false"/></style:default-style>
{''.join(styles)}
<text:outline-style style:name="Outline">
{''.join(f'<text:outline-level-style text:level="{i}" style:num-format=""><style:list-level-properties text:list-level-position-and-space-mode="label-alignment"><style:list-level-label-alignment text:label-followed-by="nothing" fo:text-indent="0mm" fo:margin-left="0mm"/></style:list-level-properties></text:outline-level-style>' for i in range(1, 11))}
</text:outline-style>
<text:notes-configuration text:note-class="footnote" style:num-format="1" text:start-value="0" text:footnotes-position="page" text:start-numbering-at="document"/>
</office:styles>
<office:automatic-styles>
<style:page-layout style:name="pm_first">
<style:page-layout-properties fo:page-width="{PAGE_W}" fo:page-height="{PAGE_H}" style:print-orientation="portrait" fo:margin-top="{MARGIN}" fo:margin-bottom="{MARGIN}" fo:margin-left="{MARGIN}" fo:margin-right="{MARGIN}" style:writing-mode="lr-tb" style:num-format="1"/>
<style:header-style/><style:footer-style/>
</style:page-layout>
<style:page-layout style:name="pm_follow">
<style:page-layout-properties fo:page-width="{PAGE_W}" fo:page-height="{PAGE_H}" style:print-orientation="portrait" fo:margin-top="{MARGIN}" fo:margin-bottom="15mm" fo:margin-left="{MARGIN}" fo:margin-right="{MARGIN}" style:writing-mode="lr-tb" style:num-format="1"/>
<style:header-style/>
<style:footer-style><style:header-footer-properties fo:min-height="10mm" fo:margin-top="5mm" fo:margin-left="0mm" fo:margin-right="0mm" style:dynamic-spacing="false"/></style:footer-style>
</style:page-layout>
</office:automatic-styles>
<office:master-styles>
<style:master-page style:name="Standard" style:display-name="Default Page Style" style:page-layout-name="pm_follow">
<style:footer><text:p text:style-name="Footer"><text:page-number text:select-page="current">2</text:page-number> / <text:page-count>2</text:page-count></text:p></style:footer>
</style:master-page>
<style:master-page style:name="First_20_Page" style:display-name="First Page" style:page-layout-name="pm_first" style:next-style-name="Standard"/>
</office:master-styles>
</office:document-styles>
"""
# Note: pm_follow's bottom margin (15 mm) + footer (5 mm gap + 10 mm body)
# leaves ~25 mm below the text on pages 2+, matching page 1's 25 mm margin.
# md2odt.py keeps that relationship when the margin is overridden.

CONTENT_XML = f"""<?xml version="1.0" encoding="UTF-8"?>
<office:document-content {NS}><office:body><office:text>
<text:p text:style-name="Document_20_Start"/>
<text:p text:style-name="Text_20_body">Style template for markdown-to-odt-letters. Content is replaced by pandoc.</text:p>
</office:text></office:body></office:document-content>
"""

META_XML = f"""<?xml version="1.0" encoding="UTF-8"?>
<office:document-meta {NS}><office:meta><meta:generator>markdown-to-odt-letters make_reference.py</meta:generator><dc:title>Letter reference template</dc:title></office:meta></office:document-meta>
"""

MANIFEST_XML = """<?xml version="1.0" encoding="UTF-8"?>
<manifest:manifest xmlns:manifest="urn:oasis:names:tc:opendocument:xmlns:manifest:1.0" manifest:version="1.3">
<manifest:file-entry manifest:full-path="/" manifest:version="1.3" manifest:media-type="application/vnd.oasis.opendocument.text"/>
<manifest:file-entry manifest:full-path="content.xml" manifest:media-type="text/xml"/>
<manifest:file-entry manifest:full-path="styles.xml" manifest:media-type="text/xml"/>
<manifest:file-entry manifest:full-path="meta.xml" manifest:media-type="text/xml"/>
</manifest:manifest>
"""


def main():
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parent.parent / "reference.odt"
    with zipfile.ZipFile(out, "w") as z:
        # mimetype must be first and uncompressed
        z.writestr(zipfile.ZipInfo("mimetype"), "application/vnd.oasis.opendocument.text",
                   compress_type=zipfile.ZIP_STORED)
        for name, data in (("content.xml", CONTENT_XML), ("styles.xml", STYLES_XML),
                           ("meta.xml", META_XML), ("META-INF/manifest.xml", MANIFEST_XML)):
            z.writestr(name, data, compress_type=zipfile.ZIP_DEFLATED)
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
