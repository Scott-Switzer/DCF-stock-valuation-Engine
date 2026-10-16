"""Read generated XLSX formulas/inputs for an independent spreadsheet evaluator."""
import json
import re
import sys
import xml.etree.ElementTree as ET
from zipfile import ZipFile

NS = '{http://schemas.openxmlformats.org/spreadsheetml/2006/main}'
with ZipFile(sys.argv[1]) as book:
    names = [s.attrib['name'] for s in ET.fromstring(book.read('xl/workbook.xml')).iter(NS + 'sheet')]
    sheets = {}
    for i, name in enumerate(names, 1):
        grid = []
        for c in ET.fromstring(book.read(f'xl/worksheets/sheet{i}.xml')).iter(NS + 'c'):
            letters, number = re.fullmatch(r'([A-Z]+)([0-9]+)', c.attrib['r']).groups()
            col = 0
            for letter in letters:
                col = col * 26 + ord(letter) - ord('A') + 1
            row = int(number) - 1
            while len(grid) <= row:
                grid.append([])
            while len(grid[row]) < col:
                grid[row].append(None)
            f, v = c.find(NS + 'f'), c.find(NS + 'v')
            if f is not None:
                value = '=' + f.text
            elif c.attrib.get('t') == 'inlineStr':
                value = ''.join(t.text or '' for t in c.iter(NS + 't'))
                # Literal text beginning '=' must not be treated as a formula.
                if value.startswith('='):
                    value = "'" + value
            else:
                value = float(v.text) if v is not None and v.text else None
            grid[row][col - 1] = value
        sheets[name] = grid
    print(json.dumps(sheets))
