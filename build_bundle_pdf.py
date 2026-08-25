#!/usr/bin/env python3
"""Build print-ready PDF of ComplianceDocs bundle from markdown templates.
Requires: fpdf2 (.venv/bin/pip install fpdf2)"""
import re, os
from fpdf import FPDF

class PDF(FPDF):
    def header(self):
        if self.page_no() > 1:
            self.set_font('Helvetica','I',8); self.set_text_color(120,120,120)
            self.cell(0,6,'ComplianceDocs Bundle', align='R'); self.ln(10)

pdf = PDF(); pdf.set_auto_page_break(True, margin=20); pdf.set_margins(20,20,20)
FILES = ['dpa-template.md','eaa-statement-template.md','nis2-contract-clauses.md','vendor-assessment-checklist.md']
TITLES = ['GDPR Data Processing Agreement','EAA Accessibility Statement','NIS2 Contract Clauses','Vendor Security Assessment Checklist']

def clean(t):
    t = re.sub(r'\*\*(.+?)\*\*', r'\1', t); t = re.sub(r'\*(.+?)\*', r'\1', t)
    for k,v in {'\u2014':'-','\u2013':'-','\u2018':"'",'\u2019':"'",'\u201c':'"','\u201d':'"','\u2022':'-','\u00a0':' ','\u2705':'[x]','\u2713':'[x]'}.items():
        t = t.replace(k,v)
    return re.sub(r'\s+',' ',t).strip()

def rx(): pdf.set_x(pdf.l_margin)

for f, title in zip(FILES, TITLES):
    pdf.add_page()
    pdf.set_font('Helvetica','B',18); pdf.set_text_color(44,82,130)
    pdf.multi_cell(0,10,clean(title)); rx(); pdf.ln(2)
    pdf.set_text_color(26,26,26)
    for line in open(f'products/{f}'):
        line = line.rstrip('\n')
        if not line.strip(): pdf.ln(3); rx(); continue
        if line.startswith('# '):
            pdf.set_font('Helvetica','B',14); rx(); pdf.multi_cell(0,8,clean(line[2:])); rx(); pdf.set_font('Helvetica','',10.5)
        elif line.startswith('## '):
            pdf.set_font('Helvetica','B',12); rx(); pdf.multi_cell(0,7,clean(line[3:])); rx(); pdf.set_font('Helvetica','',10.5)
        elif line.startswith('- ') or re.match(r'^\d+\.\s', line):
            m = re.match(r'^(\d+\.)',line); txt = clean(re.sub(r'^(- |\d+\.\s)','',line))
            prefix = '- ' if not m else m.group(1)+' '
            rx(); pdf.multi_cell(pdf.w-pdf.r_margin-pdf.l_margin-5, 6, prefix+txt); rx()
        elif re.match(r'^\|', line):
            cells=[clean(c) for c in (x.strip() for x in line.strip('|').split('|'))]
            if set(''.join(cells)) <= set('-:'): continue
            pdf.set_font('Helvetica','',9)
            for c in cells:
                if c: rx(); pdf.multi_cell(0,5,'* '+c)
            pdf.ln(1); rx(); pdf.set_font('Helvetica','',10.5)
        else:
            pdf.set_font('Helvetica','',10.5); rx(); pdf.multi_cell(0,6,clean(line)); rx()

pdf.output('products/compliance-bundle.pdf')
print("PDF:", os.path.getsize('products/compliance-bundle.pdf'), "bytes,", pdf.page_no(), "pages")
