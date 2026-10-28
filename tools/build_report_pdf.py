"""Portable PDF edition from the same DOCX content when Word is unavailable."""
import io
from pathlib import Path
from xml.sax.saxutils import escape
from docx import Document
from docx.text.paragraph import Paragraph as WordParagraph
from docx.table import Table as WordTable
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle, Image, KeepTogether
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from PIL import Image as PILImage

root=Path(__file__).resolve().parents[1]
pdfmetrics.registerFont(TTFont('Arial','C:/Windows/Fonts/arial.ttf'))
pdfmetrics.registerFont(TTFont('Arial-Bold','C:/Windows/Fonts/arialbd.ttf'))
pdfmetrics.registerFontFamily('Arial',normal='Arial',bold='Arial-Bold',italic='Arial',boldItalic='Arial-Bold')
source=Document(root/'deliverables/IDS_Project_Report_Editable.docx')
body=ParagraphStyle('body',fontName='Arial',fontSize=10,leading=14.1,spaceAfter=7,textColor=colors.black)
heading=ParagraphStyle('heading',parent=body,fontName='Arial-Bold',fontSize=21,leading=26,spaceAfter=15)
subheading=ParagraphStyle('subheading',parent=body,fontName='Arial-Bold',fontSize=12,leading=16,spaceBefore=11,spaceAfter=7,keepWithNext=True)
title=ParagraphStyle('title',parent=body,fontName='Arial-Bold',fontSize=29,leading=35,spaceAfter=18)
subtitle=ParagraphStyle('subtitle',parent=body,fontSize=14,leading=20,spaceAfter=18)
caption=ParagraphStyle('caption',parent=body,fontSize=8.5,leading=11,alignment=TA_CENTER,spaceAfter=9)
cell=ParagraphStyle('cell',parent=body,fontSize=8.7,leading=11.5,spaceAfter=0)
cellhead=ParagraphStyle('cellhead',parent=cell,fontName='Arial-Bold',textColor=colors.white)
story=[]
number=0
for element in source.element.body:
    kind=element.tag.rsplit('}',1)[-1]
    if kind=='p':
        pp=WordParagraph(element,source)
        if element.xpath('.//w:br[@w:type="page"]'):
            story.append(PageBreak()); number=0; continue
        blips=element.xpath('.//a:blip')
        if blips:
            for blip in blips:
                image=source.part.related_parts[blip.get('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}embed')].blob
                iw,ih=PILImage.open(io.BytesIO(image)).size
                width=min(448,iw*.5)
                story.append(Image(io.BytesIO(image),width=width,height=width*ih/iw))
            continue
        text=pp.text.strip()
        if not text:
            story.append(Spacer(1,6)); continue
        name=pp.style.name
        style=title if name=='Title' else subtitle if name=='Subtitle' else heading if name=='Heading 1' else subheading if name=='Heading 2' else caption if name=='Caption' else body
        text=escape(text).replace('\n','<br/>')
        if name=='List Bullet': text='• '+text
        if name=='List Number': number+=1; text=str(number)+'. '+text
        else: number=0
        story.append(Paragraph(text,style))
    elif kind=='tbl':
        wt=WordTable(element,source)
        data=[[Paragraph(escape(c.text).replace('\n','<br/>'),cellhead if i==0 else cell) for c in r.cells] for i,r in enumerate(wt.rows)]
        raw=[c.width.inches if c.width else 1 for c in wt.rows[0].cells]
        widths=[v/sum(raw)*470 for v in raw]
        tt=Table(data,colWidths=widths,repeatRows=1,hAlign='CENTER')
        commands=[('BACKGROUND',(0,0),(-1,0),colors.HexColor('#17344D')),('GRID',(0,0),(-1,-1),.45,colors.HexColor('#D9D9D9')),('VALIGN',(0,0),(-1,-1),'MIDDLE'),('LEFTPADDING',(0,0),(-1,-1),8),('RIGHTPADDING',(0,0),(-1,-1),8),('TOPPADDING',(0,0),(-1,-1),7),('BOTTOMPADDING',(0,0),(-1,-1),7)]
        for i in range(1,len(data)):
            commands.append(('BACKGROUND',(0,i),(-1,i),colors.HexColor('#EEF4F7') if i%2 else colors.white))
        tt.setStyle(TableStyle(commands));story.extend([tt,Spacer(1,9)])

def page(canvas,doc):
    if doc.page==1:return
    canvas.setFont('Arial',8);canvas.setFillColor(colors.black)
    canvas.drawString(51,811,'CSE / PDEU                                         MACHINE LEARNING LABORATORY')
    canvas.drawRightString(544,26,f'Payas Vaishnav  •  23BCP430     |     {doc.page}')

target=root/'deliverables/IDS_Project_Report.pdf'
pdf=SimpleDocTemplate(str(target),pagesize=(595.28,841.89),leftMargin=55,rightMargin=55,topMargin=55,bottomMargin=45,title='Network Intrusion Detection Using Machine Learning',author='Payas Vaishnav')
pdf.build(story,onFirstPage=page,onLaterPages=page)
print('PDF created:',target)
