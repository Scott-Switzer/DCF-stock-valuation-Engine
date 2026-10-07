"""Audited, formula-driven XLSX workbooks for DCF, DDM and relative valuations.

Stdlib only (zipfile + xml) so the writer runs unchanged on Cloudflare
Python Workers, where third-party Excel libraries are unavailable.

Conventions (per house financial-model standard):
- Blue cells: hardcoded inputs the user may change for scenarios.
- Black cells: same-sheet formulas and calculations.
- Green cells: live links pulling from another worksheet.
- Yellow fill: key assumptions needing attention (WACC, terminal growth).
- Years are text; currency $#,##0 with "-" for zero; percents 0.0%/0.00%.
- Every calculated cell is a formula; guards return "n/a", never an error.
"""

import io
import re
import zipfile
from xml.sax.saxutils import escape

FONT_BLUE = "0000FF"
FONT_GREEN = "008000"
FONT_RED = "FF0000"
FONT_GRAY = "808080"

XF_DEFAULT = 0
XF_HEADER = 1
XF_LABEL = 2
XF_IN_US = 3
XF_IN_PCT1 = 4
XF_IN_PCT2 = 5
XF_IN_TEXT = 6
XF_KEY_PCT = 7
XF_KEY_US = 8
XF_US = 9
XF_US2 = 10
XF_PCT = 11
XF_MULT = 12
XF_LINK_US = 13
XF_LINK_US2 = 14
XF_LINK_PCT = 15
XF_WARN = 16
XF_NOTE = 17
XF_LINK_TEXT = 18
XF_DEC4 = 19
XF_IN_US2 = 20


def col_letter(col):
    letters = ""
    while col > 0:
        col, rem = divmod(col - 1, 26)
        letters = chr(65 + rem) + letters
    return letters


def ref(col, row, absolute=True):
    if absolute:
        return f"${col_letter(col)}${row}"
    return f"{col_letter(col)}{row}"


class Sheet:
    def __init__(self, name):
        self.name = name
        self.cells = {}
        self.widths = {}
        self.freeze = None
        self.max_row = 0
        self.max_col = 0

    def _put(self, row, col, kind, value, style):
        self.cells[(row, col)] = (kind, value, style)
        self.max_row = max(self.max_row, row)
        self.max_col = max(self.max_col, col)

    def text(self, row, col, value, style=XF_DEFAULT):
        self._put(row, col, "s", "" if value is None else str(value), style)

    def num(self, row, col, value, style=XF_US):
        self._put(row, col, "n", value, style)

    def formula(self, row, col, expr, style=XF_US):
        self._put(row, col, "f", expr, style)

    def link(self, row, col, expr, style=XF_LINK_US):
        self.formula(row, col, expr, style)

    def width(self, col, size):
        self.widths[col] = size

    def freeze_at(self, col, row):
        self.freeze = (col, row)


def _styles_xml():
    fonts = [
        '<font><sz val="11"/><name val="Arial"/></font>',
        '<font><b/><sz val="11"/><color rgb="FFFFFFFF"/><name val="Arial"/></font>',
        f'<font><sz val="11"/><color rgb="FF{FONT_BLUE}"/><name val="Arial"/></font>',
        f'<font><sz val="11"/><color rgb="FF{FONT_GREEN}"/><name val="Arial"/></font>',
        '<font><b/><sz val="11"/><name val="Arial"/></font>',
        f'<font><sz val="11"/><color rgb="FF{FONT_RED}"/><name val="Arial"/></font>',
        f'<font><i/><sz val="9"/><color rgb="FF{FONT_GRAY}"/><name val="Arial"/></font>',
    ]
    fills = [
        '<fill><patternFill patternType="none"/></fill>',
        '<fill><patternFill patternType="gray125"/></fill>',
        '<fill><patternFill patternType="solid"><fgColor rgb="FFFFFF00"/>'
        "<bgColor indexed=\"64\"/></patternFill></fill>",
        '<fill><patternFill patternType="solid"><fgColor rgb="FF244061"/>'
        "<bgColor indexed=\"64\"/></patternFill></fill>",
    ]
    borders = ['<border><left/><right/><top/><bottom/><diagonal/></border>']
    numfmts = [
        '<numFmt numFmtId="164" formatCode="$#,##0;($#,##0);&quot;-&quot;"/>',
        '<numFmt numFmtId="165" formatCode="$#,##0.00;($#,##0.00);&quot;-&quot;"/>',
        '<numFmt numFmtId="166" formatCode="0.0%"/>',
        '<numFmt numFmtId="167" formatCode="0.00%"/>',
        '<numFmt numFmtId="168" formatCode="0.0&quot;x&quot;"/>',
        '<numFmt numFmtId="169" formatCode="0.0000"/>',
    ]
    def xf(font, fill, border, fmt, align=""):
        a = f' applyAlignment="1"><alignment{align}/>' if align else ">"
        return (
            f'<xf numFmtId="{fmt}" fontId="{font}" fillId="{fill}" '
            f'borderId="{border}" xfId="0"{a}</xf>'
        )

    xfs = [
        xf(0, 0, 0, 0),
        xf(1, 3, 0, 0, ' horizontal="center" vertical="center"'),
        xf(4, 0, 0, 0),
        xf(2, 0, 0, 164),
        xf(2, 0, 0, 166),
        xf(2, 0, 0, 167),
        xf(2, 0, 0, 49),
        xf(2, 2, 0, 167),
        xf(2, 2, 0, 164),
        xf(0, 0, 0, 164),
        xf(0, 0, 0, 165),
        xf(0, 0, 0, 167),
        xf(0, 0, 0, 168),
        xf(3, 0, 0, 164),
        xf(3, 0, 0, 165),
        xf(3, 0, 0, 167),
        xf(5, 0, 0, 0),
        xf(6, 0, 0, 0),
        xf(3, 0, 0, 0),
        xf(0, 0, 0, 169),
        xf(2, 0, 0, 165),
    ]
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        f"<numFmts count=\"{len(numfmts)}\">{''.join(numfmts)}</numFmts>"
        f"<fonts count=\"{len(fonts)}\">{''.join(fonts)}</fonts>"
        f"<fills count=\"{len(fills)}\">{''.join(fills)}</fills>"
        f"<borders count=\"{len(borders)}\">{''.join(borders)}</borders>"
        '<cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" '
        'borderId="0" xfId="0"/></cellStyleXfs>'
        f"<cellXfs count=\"{len(xfs)}\">{''.join(xfs)}</cellXfs>"
        '<cellStyles count="1"><cellStyle name="Normal" xfId="0" builtinId="0"/>'
        "</cellStyles></styleSheet>"
    )


def _sheet_xml(sheet):
    parts = [
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">',
    ]
    if sheet.max_row and sheet.max_col:
        parts.append(
            f"<dimension ref=\"A1:{col_letter(sheet.max_col)}{sheet.max_row}\"/>"
        )
    parts.append("<sheetViews><sheetView workbookViewId=\"0\">")
    if sheet.freeze:
        col, row = sheet.freeze
        cell = f"{col_letter(col)}{row}"
        parts.append(
            f'<pane xSplit="{col - 1}" ySplit="{row - 1}" topLeftCell="{cell}" '
            'activePane="bottomRight" state="frozen"/>'
        )
    parts.append("</sheetView></sheetViews>")
    parts.append('<sheetFormat defaultRowHeight="15"/>')
    if sheet.widths:
        cols = "".join(
            f'<col min="{c}" max="{c}" width="{w}" customWidth="1"/>'
            for c, w in sorted(sheet.widths.items())
        )
        parts.append(f"<cols>{cols}</cols>")
    parts.append("<sheetData>")
    by_row = {}
    for (r, c), cell in sheet.cells.items():
        by_row.setdefault(r, []).append((c, cell))
    for r in sorted(by_row):
        parts.append(f'<row r="{r}">')
        for c, (kind, value, style) in sorted(by_row[r]):
            addr = f"{col_letter(c)}{r}"
            if kind == "s":
                parts.append(
                    f'<c r="{addr}" t="inlineStr" s="{style}"><is><t xml:space='
                    f"\"preserve\">{escape(value)}</t></is></c>"
                )
            elif kind == "n":
                parts.append(f'<c r="{addr}" s="{style}"><v>{value!r}</v></c>')
            else:
                expr = value[1:] if value.startswith("=") else value
                parts.append(
                    f'<c r="{addr}" s="{style}"><f>{escape(expr)}</f></c>'
                )
        parts.append("</row>")
    parts.append("</sheetData></worksheet>")
    return "".join(parts)


def build_workbook(sheets, title="Valuation"):
    _ = title
    out = io.BytesIO()
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr(
            "[Content_Types].xml",
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Types xmlns="http://schemas.openxmlformats.org/package/2006/'
            'content-types">'
            '<Default Extension="rels" ContentType="application/vnd.openxml'
            "formats-package.relationships+xml\"/>"
            '<Default Extension="xml" ContentType="application/xml"/>'
            '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.'
            'openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
            '<Override PartName="/xl/styles.xml" ContentType="application/vnd.'
            'openxmlformats-officedocument.spreadsheetml.styles+xml"/>'
            + "".join(
                f'<Override PartName="/xl/worksheets/sheet{i + 1}.xml" '
                "ContentType=\"application/vnd.openxmlformats-officedocument."
                'spreadsheetml.worksheet+xml"/>'
                for i in range(len(sheets))
            )
            + "</Types>",
        )
        z.writestr(
            "_rels/.rels",
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/'
            '2006/relationships"><Relationship Id="rId1" Type="http://schemas.'
            "openxmlformats.org/officeDocument/2006/relationships/officeDocument"
            '" Target="xl/workbook.xml"/></Relationships>',
        )
        sheet_refs = "".join(
            f'<sheet name="{escape(s.name)}" sheetId="{i + 1}" '
            f'r:id="rId{i + 1}"/>'
            for i, s in enumerate(sheets)
        )
        z.writestr(
            "xl/workbook.xml",
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/'
            '2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument'
            '/2006/relationships"><calcPr fullCalcOnLoad="1"/><sheets>'
            f"{sheet_refs}</sheets></workbook>",
        )
        z.writestr(
            "xl/_rels/workbook.xml.rels",
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/'
            '2006/relationships">'
            + "".join(
                '<Relationship Id="rId'
                f"{i + 1}\" Type=\"http://schemas.openxmlformats.org/"
                'officeDocument/2006/relationships/worksheet" '
                f'Target="worksheets/sheet{i + 1}.xml"/>'
                for i in range(len(sheets))
            )
            + '<Relationship Id="rId'
            f"{len(sheets) + 1}\" Type=\"http://schemas.openxmlformats.org/"
            'officeDocument/2006/relationships/styles" Target="styles.xml"/>'
            "</Relationships>",
        )
        z.writestr("xl/styles.xml", _styles_xml())
        for i, s in enumerate(sheets):
            z.writestr(f"xl/worksheets/sheet{i + 1}.xml", _sheet_xml(s))
    out.seek(0)
    return out.read()


def _cover(sheet, title, doc, outputs):
    sheet.text(1, 1, title, XF_HEADER)
    sheet.text(1, 2, "Value", XF_HEADER)
    sheet.width(1, 34)
    sheet.width(2, 28)
    sheet.text(2, 1, "Company", XF_LABEL)
    sheet.text(2, 2, doc["company"].get("name", ""), XF_IN_TEXT)
    sheet.text(3, 1, "Ticker", XF_LABEL)
    sheet.text(3, 2, doc["company"].get("ticker", ""), XF_IN_TEXT)
    sheet.text(4, 1, "Valuation date", XF_LABEL)
    sheet.text(4, 2, doc.get("valuation_date", ""), XF_IN_TEXT)
    sheet.text(5, 1, "Source", XF_LABEL)
    sheet.text(5, 2, doc["source"].get("name", ""), XF_IN_TEXT)
    sheet.text(6, 1, "Units", XF_LABEL)
    sheet.text(6, 2, "Absolute USD; rates are decimals", XF_NOTE)
    row = 8
    sheet.text(row, 1, "Key outputs (live links)", XF_LABEL)
    row += 1
    for label, cell_ref, style in outputs:
        sheet.text(row, 1, label)
        sheet.link(row, 2, cell_ref, style)
        row += 1
    row += 1
    sheet.text(
        row,
        1,
        "Blue cells are editable assumptions. Black cells are formulas. "
        "Green cells link across sheets.",
        XF_NOTE,
    )


def _provenance(sheet, doc, warnings, start_warnings=2):
    sheet.text(1, 1, "Assumption / limitation", XF_HEADER)
    sheet.width(1, 110)
    row = start_warnings
    for w in warnings + doc["source"].get("warnings", []):
        sheet.text(row, 1, w, XF_WARN)
        row += 1
    row += 1
    sheet.text(row, 1, "Source record (JSON)", XF_LABEL)
    row += 1
    import json as _json

    sheet.text(row, 1, _json.dumps(doc["source"]), XF_NOTE)
    for h in doc.get("historical", []):
        row += 1
        sheet.text(
            row,
            1,
            f"{h.get('period_end')}: {str(h.get('provenance', {}))}",
            XF_NOTE,
        )


def _audit_sheet(name, steps):
    sheet = Sheet(name)
    sheet.text(1, 1, "Calculation step", XF_HEADER)
    sheet.text(1, 2, "Value (live)", XF_HEADER)
    sheet.text(1, 3, "Formula", XF_HEADER)
    sheet.text(1, 4, "What this means", XF_HEADER)
    sheet.width(1, 30)
    sheet.width(2, 20)
    sheet.width(3, 52)
    sheet.width(4, 64)
    sheet.freeze_at(2, 2)
    for i, (label, value_ref, formula_text, meaning, style) in enumerate(steps, start=2):
        sheet.text(i, 1, label)
        sheet.link(i, 2, value_ref, style)
        sheet.text(i, 3, formula_text, XF_NOTE)
        sheet.text(i, 4, meaning, XF_NOTE)
    return sheet


def _assumption_block(sheet, rows):
    for row, label, value, style in rows:
        sheet.text(row, 1, label)
        if isinstance(value, str):
            sheet.text(row, 2, value, style)
        else:
            sheet.num(row, 2, value, style)


def dcf_workbook(doc, a, r):
    hist = doc["historical"]
    periods = [h["period_end"] for h in hist]

    assum = Sheet("Assumptions")
    assum.text(1, 1, "Assumption", XF_HEADER)
    assum.text(1, 2, "Value", XF_HEADER)
    assum.width(1, 30)
    assum.width(2, 22)
    assum.freeze_at(2, 2)
    _assumption_block(
        assum,
        [
            (2, "WACC override", a.get("wacc_override", r["wacc"]), XF_KEY_PCT),
            (3, "Terminal growth", a["terminal_growth_rate"], XF_KEY_PCT),
            (4, "Terminal mode", a.get("terminal_mode", "template"), XF_IN_TEXT),
            (5, "Terminal ROIC", a.get("terminal_roic") or 0.10, XF_IN_PCT2),
            (6, "Revenue growth YoY", "", XF_LABEL),
            *[
                (7 + i, f"Year {i + 1}", a["revenue_growth_rates"][i], XF_IN_PCT1)
                for i in range(5)
            ],
            (12, "EBIT / revenue", "", XF_LABEL),
            *[
                (13 + i, f"Year {i + 1}", a["ebit_margins"][i], XF_IN_PCT1)
                for i in range(5)
            ],
            (18, "D&A / revenue", "", XF_LABEL),
            *[(19 + i, f"Year {i + 1}", a["da_margins"][i], XF_IN_PCT1) for i in range(5)],
            (24, "CapEx / revenue", "", XF_LABEL),
            *[
                (25 + i, f"Year {i + 1}", a["capex_margins"][i], XF_IN_PCT1)
                for i in range(5)
            ],
            (30, "NWC / revenue", "", XF_LABEL),
            *[
                (31 + i, f"Year {i + 1}", a["nwc_margins"][i], XF_IN_PCT1)
                for i in range(5)
            ],
            (36, "Tax rate", "", XF_LABEL),
            *[(37 + i, f"Year {i + 1}", a["tax_rates"][i], XF_IN_PCT1) for i in range(5)],
            (42, "Net income / revenue (display)", "", XF_LABEL),
            *[
                (43 + i, f"Year {i + 1}", a["net_income_margins"][i], XF_IN_PCT1)
                for i in range(5)
            ],
            (48, "Book value / revenue (display)", "", XF_LABEL),
            *[
                (49 + i, f"Year {i + 1}", a["book_value_margins"][i], XF_IN_PCT1)
                for i in range(5)
            ],
            (54, "12-month bridge overrides", "", XF_LABEL),
            (55, "Future debt", r["future_bridge"]["debt"], XF_IN_US),
            (56, "Future cash", r["future_bridge"]["cash"], XF_IN_US),
            (57, "Future shares", r["future_bridge"]["shares"], XF_IN_US),
            (58, "Future preferred", r["future_bridge"]["preferred"], XF_IN_US),
            (59, "Future minority", r["future_bridge"]["minority"], XF_IN_US),
            (60, "Future other assets", r["future_bridge"]["other_assets"], XF_IN_US),
        ],
    )
    W, G = "Assumptions!$B$2", "Assumptions!$B$3"
    gr = [f"Assumptions!$B${7 + i}" for i in range(5)]
    eb = [f"Assumptions!$B${13 + i}" for i in range(5)]
    da = [f"Assumptions!$B${19 + i}" for i in range(5)]
    cx = [f"Assumptions!$B${25 + i}" for i in range(5)]
    nw = [f"Assumptions!$B${31 + i}" for i in range(5)]
    tx = [f"Assumptions!$B${37 + i}" for i in range(5)]

    hist_sheet = Sheet("Historical")
    hist_sheet.text(1, 1, "Line item (absolute USD)", XF_HEADER)
    hist_sheet.text(1, 2, "Notes", XF_HEADER)
    for j, p in enumerate(periods):
        hist_sheet.text(1, 3 + j, str(p), XF_HEADER)
    hist_sheet.width(1, 30)
    hist_sheet.width(2, 24)
    for j in range(3):
        hist_sheet.width(3 + j, 20)
    hist_sheet.freeze_at(2, 2)
    fields = [
        (2, "revenue", XF_IN_US),
        (3, "ebit", XF_IN_US),
        (4, "net_income", XF_IN_US),
        (5, "capex", XF_IN_US),
        (6, "d_and_a", XF_IN_US),
        (7, "nwc", XF_IN_US),
        (8, "book_value", XF_IN_US),
        (9, "tax_rate", XF_IN_PCT2),
    ]
    labels = {
        "revenue": "Revenue",
        "ebit": "EBIT",
        "net_income": "Net income",
        "capex": "Capital expenditures",
        "d_and_a": "Depreciation & amortization",
        "nwc": "Operating net working capital",
        "book_value": "Book value",
        "tax_rate": "Effective tax rate",
    }
    for row, key, style in fields:
        hist_sheet.text(row, 1, labels[key])
        for j in range(3):
            hist_sheet.num(row, 3 + j, hist[j][key], style)
    hist_sheet.text(11, 1, f"Bridge (as of {doc['bridge'].get('as_of', '')})", XF_LABEL)
    for i, (key, label) in enumerate(
        [
            ("short_term_debt", "Short-term debt"),
            ("long_term_debt", "Long-term debt"),
            ("cash", "Cash & equivalents"),
            ("preferred_equity", "Preferred claims"),
            ("minority_interest", "Noncontrolling interests"),
            ("other_nonoperating_assets", "Other nonoperating assets"),
        ]
    ):
        hist_sheet.text(12 + i, 1, label)
        for j in range(3):
            hist_sheet.num(12 + i, 3 + j, doc["bridge"][key], XF_IN_US)
    hist_sheet.text(19, 1, "Market price")
    hist_sheet.num(19, 5, doc["market"]["price"], XF_IN_US2)
    hist_sheet.text(20, 1, "Diluted shares")
    hist_sheet.num(20, 5, doc["market"]["diluted_shares"], XF_IN_US)
    hist_sheet.text(21, 1, "Price as of")
    hist_sheet.text(21, 5, str(doc["market"].get("price_as_of", "")), XF_IN_TEXT)
    H = "Historical!"
    REV3, NWC3 = f"{H}$E$2", f"{H}$E$7"
    CASH, STD, LTD = f"{H}$E$14", f"{H}$E$12", f"{H}$E$13"
    PREF, MINO, OTH = f"{H}$E$15", f"{H}$E$16", f"{H}$E$17"
    PRICE, SHARES = f"{H}$E$19", f"{H}$E$20"

    def xl_link(expr):
        return "link" if "!" in expr else "calc"

    model = Sheet("Model")
    model.text(1, 1, "Line item (absolute USD)", XF_HEADER)
    for i in range(5):
        model.text(1, 2 + i, f"Year {i + 1}", XF_HEADER)
    model.width(1, 30)
    for i in range(5):
        model.width(2 + i, 20)
    model.freeze_at(2, 2)
    items = [
        "Revenue",
        "EBIT",
        "Taxes",
        "NOPAT",
        "D&A",
        "CapEx",
        "NWC",
        "Change in NWC",
        "UFCF",
        "Discount factor",
        "PV of UFCF",
    ]
    for i, label in enumerate(items, start=2):
        model.text(i, 1, label)
    cols = [col_letter(2 + i) for i in range(5)]
    formulas = {}
    for i, L in enumerate(cols):
        P = cols[i - 1] if i else None
        rev = f"={REV3}*(1+{gr[i]})" if P is None else f"={P}2*(1+{gr[i]})"
        nwc = f"={L}2*{nw[i]}"
        dnwc = f"={L}8-{NWC3}" if P is None else f"={L}8-{P}8"
        block = {
            2: rev,
            3: f"={L}2*{eb[i]}",
            4: f"={L}3*{tx[i]}",
            5: f"={L}3-{L}4",
            6: f"={L}2*{da[i]}",
            7: f"={L}2*{cx[i]}",
            8: nwc,
            9: dnwc,
            10: f"={L}5+{L}6-{L}7-{L}9",
            11: f"=1/(1+{W})^{i + 1}",
            12: f"={L}10*{L}11",
        }
        for row, expr in block.items():
            formulas[(row, L)] = expr
    tv = (
        f"=IF(Assumptions!$B$4=\"normalized\",F5*(1+{G})*(1-{G}/"
        f"Assumptions!$B$5)/({W}-{G}),F10*(1+{G})/({W}-{G}))"
    )
    summary = {
        14: ("Stage-1 PV", "=SUM(B12:F12)"),
        15: ("Terminal FCFF", tv),
        16: ("PV of terminal value", f"=B15/(1+{W})^5"),
        17: ("Enterprise value", "=B14+B16"),
        18: ("(+) Cash", f"={CASH}"),
        19: ("(-) Debt", f"=-({STD}+{LTD})"),
        20: ("(-) Preferred", f"=-{PREF}"),
        21: ("(-) Noncontrolling", f"=-{MINO}"),
        22: ("(+) Other assets", f"={OTH}"),
        23: ("Equity value", "=SUM(B17:B22)"),
        24: ("(÷) Diluted shares", f"={SHARES}"),
        25: ("Intrinsic value per share", '=IF(B24=0,"n/a",B23/B24)'),
        27: (
            "EV, 12-month",
            f"=C10/(1+{W})+D10/(1+{W})^2+E10/(1+{W})^3+F10/(1+{W})^4"
            f"+B15/(1+{W})^4",
        ),
        28: ("(-) Future debt", "=-Assumptions!$B$55"),
        29: ("(+) Future cash", "=Assumptions!$B$56"),
        30: ("(-) Future preferred", "=-Assumptions!$B$58"),
        31: ("(-) Future minority", "=-Assumptions!$B$59"),
        32: ("(+) Future other", "=Assumptions!$B$60"),
        33: ("Equity, 12-month", "=SUM(B27:B32)"),
        34: ("Shares, 12-month", "=Assumptions!$B$57"),
        35: ("Target price, 12-month", '=IF(B34=0,"n/a",B33/B34)'),
        37: ("Upside today", f'=IF({PRICE}=0,"n/a",B25/{PRICE}-1)'),
        38: ("Upside, 12-month", f'=IF({PRICE}=0,"n/a",B35/{PRICE}-1)'),
        40: ("Terminal share of EV", '=IF(B17=0,"n/a",B16/B17)'),
    }
    pct_rows = {37, 38, 40}
    bold = {10, 12, 14, 17, 23, 25, 33, 35}
    for (row, L), expr in formulas.items():
        style = XF_DEC4 if row == 11 else (XF_LINK_US if "!" in expr else XF_US)
        if row in bold:
            style = XF_LABEL if L == "A" else style
        model.formula(row, 2 + cols.index(L), expr, style)
    for i in (10, 12):
        model.text(i, 1, items[i - 2], XF_LABEL)
    for row, label in [(14, "Stage-1 PV"), (17, "Enterprise value")]:
        model.text(row, 1, label, XF_LABEL)
    for row, (label, expr) in summary.items():
        if row not in (14, 17):
            model.text(row, 1, label, XF_LABEL if row in bold else XF_DEFAULT)
        kind = xl_link(expr)
        if row in pct_rows:
            style = XF_LINK_PCT if kind == "link" else XF_PCT
        elif row == 11:
            style = XF_DEC4
        else:
            style = XF_LINK_US if kind == "link" else XF_US
        model.formula(row, 2, expr, style)

    sens = Sheet("Sensitivity")
    sens.text(1, 1, "Ke \\ g", XF_HEADER)
    deltas = [-0.01, -0.005, 0, 0.005, 0.01]
    for j, d in enumerate(deltas):
        sens.formula(1, 2 + j, f"={G}{d:+g}", XF_LINK_PCT)
    for i, d in enumerate(deltas):
        sens.formula(2 + i, 1, f"={W}{d:+g}", XF_LINK_PCT)
    sens.width(1, 14)
    for j in range(5):
        sens.width(2 + j, 18)
    for i in range(5):
        for j in range(5):
            w, g = f"$A{2 + i}", f"{col_letter(2 + j)}$1"
            stage = "+".join(f"Model!${c}$10/(1+{w})^{k + 1}" for k, c in enumerate(cols))
            tv_cell = (
                f'IF(Assumptions!$B$4="normalized",Model!$F$5*(1+{g})*(1-{g}/'
                f"Assumptions!$B$5)/({w}-{g}),Model!$F$10*(1+{g})/({w}-{g}))"
            )
            eq = (
                f"({stage}+({tv_cell})/(1+{w})^5"
                f"-({STD}+{LTD})+{CASH}-{PREF}-{MINO}+{OTH})"
            )
            sens.formula(
                2 + i,
                2 + j,
                f'=IF(OR({w}<={g},{SHARES}=0),"n/a",({eq})/{SHARES})',
                XF_LINK_US2,
            )

    audit = _audit_sheet(
        "Audit",
        [
            ("Base revenue (last history)", REV3, REV3, "Starting point; never zero-filled.", XF_LINK_US),
            *[
                (f"UFCF year {i + 1}", f"Model!{c}10", formulas[(10, c)],
                 "NOPAT + D&A - CapEx - change in NWC.", XF_LINK_US)
                for i, c in enumerate(cols)
            ],
            ("Stage-1 PV", "Model!B14", "=SUM(B12:F12)", "Discounted years 1-5 at WACC.", XF_LINK_US),
            ("Terminal FCFF", "Model!B15", tv, "Template grows Y5 FCFF; normalized reinvests via ROIC.", XF_LINK_US),
            ("Terminal PV", "Model!B16", summary[16][1], "Terminal value discounted 5 years.", XF_LINK_US),
            ("Enterprise value", "Model!B17", "=B14+B16", "Value of the whole firm.", XF_LINK_US),
            ("Equity value", "Model!B23", "=SUM(B17:B22)", "EV adjusted for the current bridge.", XF_LINK_US),
            ("Intrinsic per share", "Model!B25", summary[25][1], "Equity over diluted shares; floored inputs guarded.", XF_LINK_US2),
            ("EV, 12-month", "Model!B27", summary[27][1], "Years 2-5 plus terminal, one year closer.", XF_LINK_US),
            ("Target, 12-month", "Model!B35", summary[35][1], "Forward equity over future shares.", XF_LINK_US2),
        ],
    )

    prov = Sheet("Provenance")
    _provenance(prov, doc, r["warnings"])

    cover = Sheet("Cover")
    _cover(
        cover,
        f"DCF valuation — {doc['company'].get('ticker', '')}",
        doc,
        [
            ("Intrinsic value today", "Model!B25", XF_LINK_US2),
            ("12-month target", "Model!B35", XF_LINK_US2),
            ("Enterprise value", "Model!B17", XF_LINK_US),
            ("WACC", "Assumptions!B2", XF_LINK_PCT),
        ],
    )
    return build_workbook([cover, assum, hist_sheet, model, sens, audit, prov])


def ddm_workbook(doc, a, r):
    assum = Sheet("Assumptions")
    assum.text(1, 1, "Assumption", XF_HEADER)
    assum.text(1, 2, "Value", XF_HEADER)
    assum.width(1, 30)
    assum.width(2, 22)
    _assumption_block(
        assum,
        [
            (2, "Required return (Ke)", a["required_return"], XF_KEY_PCT),
            (3, "Terminal dividend growth", a["terminal_growth_rate"], XF_KEY_PCT),
            *[
                (4 + i, f"Dividend growth Y{i + 1}", a["dividend_growth_rates"][i], XF_IN_PCT1)
                for i in range(5)
            ],
            (10, "Future shares (blank = unchanged)",
             "" if a.get("future_shares") is None else a["future_shares"], XF_IN_US),
        ],
    )
    KE, GT = "Assumptions!$B$2", "Assumptions!$B$3"
    dg = [f"Assumptions!$B${4 + i}" for i in range(5)]

    inputs = Sheet("Inputs")
    inputs.text(1, 1, "Input", XF_HEADER)
    inputs.text(1, 2, "Value", XF_HEADER)
    inputs.width(1, 30)
    inputs.width(2, 24)
    inputs.text(2, 1, "Base common dividends")
    inputs.num(2, 2, doc["base_common_dividends"], XF_IN_US)
    inputs.text(3, 1, "Dividend as of")
    inputs.text(3, 2, str(doc.get("dividend_as_of", "")), XF_IN_TEXT)
    inputs.text(4, 1, "Market price")
    inputs.num(4, 2, doc["market"]["price"], XF_IN_US2)
    inputs.text(5, 1, "Diluted shares")
    inputs.num(5, 2, doc["market"]["diluted_shares"], XF_IN_US)
    BASE, SH = "Inputs!$B$2", "Inputs!$B$5"

    model = Sheet("Model")
    model.text(1, 1, "Line item (absolute USD)", XF_HEADER)
    cols = [col_letter(2 + i) for i in range(5)]
    for i in range(5):
        model.text(1, 2 + i, f"Year {i + 1}", XF_HEADER)
    model.width(1, 30)
    for i in range(5):
        model.width(2 + i, 20)
    model.freeze_at(2, 2)
    model.text(2, 1, "Dividends")
    model.text(3, 1, "PV of dividends")
    for i, L in enumerate(cols):
        prev = f"{cols[i - 1]}2" if i else BASE
        model.formula(2, 2 + i, f"={prev}*(1+{dg[i]})", XF_LINK_US)
        model.formula(3, 2 + i, f"={L}2/(1+{KE})^{i + 1}", XF_US)
    rows = {
        5: ("Stage-1 PV", "=SUM(B3:F3)"),
        6: ("Terminal dividend value", f"=F2*(1+{GT})/({KE}-{GT})"),
        7: ("PV of terminal", f"=B6/(1+{KE})^5"),
        8: ("Equity value", "=B5+B7"),
        9: ("(÷) Diluted shares", f"={SH}"),
        10: ("Intrinsic value per share", '=IF(B9=0,"n/a",B8/B9)'),
        12: ("Stage-1 PV, 12-month (ex-div)",
              f"=C2/(1+{KE})+D2/(1+{KE})^2+E2/(1+{KE})^3+F2/(1+{KE})^4"),
        13: ("PV of terminal, 12-month", f"=B6/(1+{KE})^4"),
        14: ("Equity, 12-month", "=B12+B13"),
        15: ("Shares, 12-month", '=IF(Assumptions!$B$10="",Inputs!$B$5,Assumptions!$B$10)'),
        16: ("Target, 12-month", '=IF(B15=0,"n/a",B14/B15)'),
    }
    for row, (label, expr) in rows.items():
        model.text(row, 1, label, XF_LABEL if row in (8, 10, 14, 16) else XF_DEFAULT)
        model.formula(row, 2, expr, XF_LINK_US if "!" in expr else XF_US)

    sens = Sheet("Sensitivity")
    sens.text(1, 1, "Ke \\ g", XF_HEADER)
    deltas = [-0.01, -0.005, 0, 0.005, 0.01]
    for j, d in enumerate(deltas):
        sens.formula(1, 2 + j, f"={GT}{d:+g}", XF_LINK_PCT)
    for i, d in enumerate(deltas):
        sens.formula(2 + i, 1, f"={KE}{d:+g}", XF_LINK_PCT)
    sens.width(1, 14)
    for j in range(5):
        sens.width(2 + j, 20)
    for i in range(5):
        for j in range(5):
            ke, g = f"$A{2 + i}", f"{col_letter(2 + j)}$1"
            stage = "+".join(f"Model!${c}$2/(1+{ke})^{k + 1}" for k, c in enumerate(cols))
            sens.formula(
                2 + i, 2 + j,
                f'=IF(OR({ke}<=0,{g}>={ke},{g}<=-1),"n/a",'
                f"(({stage})+Model!$F$2*(1+{g})/({ke}-{g})/(1+{ke})^5)/{SH})",
                XF_LINK_US2,
            )

    audit = _audit_sheet(
        "Audit",
        [
            ("Base dividends", BASE, BASE, "Latest annual common dividends.", XF_LINK_US),
            ("Stage-1 PV", "Model!B5", "=SUM(B3:F3)", "Discounted years 1-5 at Ke.", XF_LINK_US),
            ("Terminal value", "Model!B6", rows[6][1], "Gordon growth on Y5 dividends.", XF_LINK_US),
            ("Intrinsic per share", "Model!B10", rows[10][1], "Equity over diluted shares.", XF_LINK_US2),
            ("Target, 12-month", "Model!B16", rows[16][1], "Ex-dividend year-one scenario.", XF_LINK_US2),
        ],
    )
    prov = Sheet("Provenance")
    _provenance(prov, doc, r["warnings"])
    cover = Sheet("Cover")
    _cover(
        cover,
        f"DDM valuation — {doc['company'].get('ticker', '')}",
        doc,
        [
            ("Intrinsic value today", "Model!B10", XF_LINK_US2),
            ("12-month target", "Model!B16", XF_LINK_US2),
            ("Required return", "Assumptions!B2", XF_LINK_PCT),
        ],
    )
    return build_workbook([cover, assum, inputs, model, sens, audit, prov])


def relative_workbook(doc, a, r):
    from suite_models import MULTIPLES

    keys = list(MULTIPLES)
    peers = doc["comparables"]
    n = len(peers)

    inputs = Sheet("Inputs")
    inputs.text(1, 1, "Target input", XF_HEADER)
    inputs.text(1, 2, "Value", XF_HEADER)
    inputs.width(1, 30)
    inputs.width(2, 22)
    row = 2
    metric_rows = {}
    for period in ["historical", "forward"]:
        inputs.text(row, 1, period.capitalize(), XF_LABEL)
        row += 1
        for key in keys:
            metric = MULTIPLES[key][1]
            val = doc["target"][period].get(metric)
            inputs.text(row, 1, f"{period} {metric}")
            if val is None:
                inputs.text(row, 2, "n/a", XF_IN_TEXT)
            else:
                inputs.num(row, 2, val, XF_IN_US)
            metric_rows[(period, metric)] = row
            row += 1
    inputs.text(row, 1, "Equity bridge", XF_LABEL)
    row += 1
    bridge_rows = {}
    for key, label in [
        ("short_term_debt", "Short-term debt"),
        ("long_term_debt", "Long-term debt"),
        ("cash", "Cash & equivalents"),
        ("preferred_equity", "Preferred claims"),
        ("minority_interest", "Noncontrolling interests"),
        ("other_nonoperating_assets", "Other nonoperating assets"),
    ]:
        inputs.text(row, 1, label)
        inputs.num(row, 2, doc["bridge"][key], XF_IN_US)
        bridge_rows[key] = row
        row += 1
    inputs.text(row, 1, "Market price")
    inputs.num(row, 2, doc["market"]["price"], XF_IN_US2)
    price_row = row
    row += 1
    inputs.text(row, 1, "Diluted shares")
    inputs.num(row, 2, doc["market"]["diluted_shares"], XF_IN_US)
    shares_row = row
    PR, SH = f"Inputs!$B${price_row}", f"Inputs!$B${shares_row}"

    peer_sheet = Sheet("Peers")
    peer_sheet.text(1, 1, "Ticker", XF_HEADER)
    peer_sheet.text(1, 2, "Name", XF_HEADER)
    for j, key in enumerate(keys):
        peer_sheet.text(1, 3 + j, MULTIPLES[key][0], XF_HEADER)
    peer_sheet.width(1, 12)
    peer_sheet.width(2, 26)
    for j in range(len(keys)):
        peer_sheet.width(3 + j, 16)
    peer_sheet.freeze_at(3, 2)
    for i, p in enumerate(peers):
        peer_sheet.text(2 + i, 1, p["ticker"], XF_IN_TEXT)
        peer_sheet.text(2, 2, "", XF_DEFAULT)
        peer_sheet.text(2 + i, 2, p.get("name", ""), XF_IN_TEXT)
        for j, key in enumerate(keys):
            val = p["multiples"].get(key)
            if val is None:
                peer_sheet.text(2 + i, 3 + j, "n/a", XF_IN_TEXT)
            else:
                peer_sheet.num(2 + i, 3 + j, val, XF_IN_US2)
    last_peer = 1 + n

    model = Sheet("Model")
    headers = ["Multiple", "Peer mean", "Forward metric", "Implied price", "Included"]
    for j, h in enumerate(headers):
        model.text(1, 1 + j, h, XF_HEADER)
    model.width(1, 18)
    for j in range(1, 5):
        model.width(1 + j, 18)
    model.freeze_at(2, 2)
    claims = (
        f"Inputs!$B${bridge_rows['short_term_debt']}"
        f"+Inputs!$B${bridge_rows['long_term_debt']}"
        f"+Inputs!$B${bridge_rows['preferred_equity']}"
        f"+Inputs!$B${bridge_rows['minority_interest']}"
        f"-Inputs!$B${bridge_rows['cash']}"
        f"-Inputs!$B${bridge_rows['other_nonoperating_assets']}"
    )
    for i, key in enumerate(keys):
        rr = 2 + i
        col = col_letter(3 + i)
        rng = f"Peers!${col}$2:${col}${last_peer}"
        model.text(rr, 1, MULTIPLES[key][0])
        model.formula(rr, 2, f"=SUMIF({rng},\">0\")/COUNTIF({rng},\">0\")", XF_LINK_US2)
        metric = MULTIPLES[key][1]
        fwd = f"Inputs!$B${metric_rows[('forward', metric)]}"
        model.link(rr, 3, fwd, XF_LINK_US)
        if key.startswith("ev_"):
            implied = f"=(B{rr}*{fwd}-({claims}))/{SH}"
        else:
            implied = f"=(B{rr}*{fwd})/{SH}"
        model.formula(rr, 4, f"=MAX(0,{implied})", XF_US2)
        model.text(rr, 5, "yes" if key in a["included_methods"] else "no", XF_IN_TEXT)
    trow = 2 + len(keys) + 1
    model.text(trow, 1, "Net common claims", XF_LABEL)
    model.formula(trow, 2, f"=({claims})", XF_LINK_US)
    model.text(trow + 1, 1, "12-month target (mean of included)", XF_LABEL)
    included_cells = ",".join(
        f"D{2 + i}" for i, key in enumerate(keys) if key in a["included_methods"]
    )
    model.formula(trow + 1, 2, f"=AVERAGE({included_cells})", XF_LINK_US2)
    model.text(trow + 2, 1, "Upside vs market")
    model.formula(trow + 2, 2, f'=IF({PR}=0,"n/a",B{trow + 1}/{PR}-1)', XF_LINK_PCT)

    audit = _audit_sheet(
        "Audit",
        [
            ("Net common claims", f"Model!B{trow}", f"=({claims})",
             "Debt-like claims minus cash-like assets.", XF_LINK_US),
            ("12-month target", f"Model!B{trow + 1}", f"=AVERAGE({included_cells})",
             "Equal-weighted mean of included implied prices.", XF_LINK_US2),
        ],
    )
    prov = Sheet("Provenance")
    _provenance(prov, doc, r["warnings"])
    cover = Sheet("Cover")
    _cover(
        cover,
        f"Relative valuation — {doc['company'].get('ticker', '')}",
        doc,
        [("12-month target", f"Model!B{trow + 1}", XF_LINK_US2)],
    )
    return build_workbook([cover, inputs, peer_sheet, model, audit, prov])


_SAFE_NAME = re.compile(r"[^A-Z0-9]+")
