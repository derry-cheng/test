"""Build publication-sized SVG/PDF and editable draw.io diagrams.

All dimensions are points: included at native width, body labels are 8.5 pt.
Draw.io stores editable native boxes, text, and orthogonal edges. SVG/PDF
exports are generated from the same specification, without rasterization.
"""
from pathlib import Path
from html import escape
import subprocess
import xml.etree.ElementTree as ET
P=Path(__file__).resolve().parent

def build(stem,width,height,boxes,edges,notes=()):
    svg=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}pt" height="{height}pt" viewBox="0 0 {width} {height}">', '<defs><marker id="arrow" markerWidth="6" markerHeight="6" refX="5.5" refY="3" orient="auto" markerUnits="userSpaceOnUse"><path d="M0,0 L6,3 L0,6 Z" fill="#334155"/></marker></defs>']
    mx=ET.Element('mxfile',host='app.diagrams.net',version='24.7.17',type='device'); dg=ET.SubElement(mx,'diagram',id=stem,name=stem)
    gm=ET.SubElement(dg,'mxGraphModel',page='1',pageScale='1',pageWidth=str(width),pageHeight=str(height),grid='1',gridSize='5')
    root=ET.SubElement(gm,'root');ET.SubElement(root,'mxCell',id='0');ET.SubElement(root,'mxCell',id='1',parent='0')
    for id,x,y,w,h,title,lines,fill in boxes:
        svg.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="3" fill="{fill}" stroke="#475569" stroke-width="0.65"/>')
        svg.append(f'<text x="{x+w/2}" y="{y+14}" text-anchor="middle" font-family="DejaVu Sans" font-size="9" font-weight="bold" fill="#0f172a">{escape(title)}</text>')
        for i,line in enumerate(lines):
            svg.append(f'<text x="{x+w/2}" y="{y+29+i*11}" text-anchor="middle" font-family="DejaVu Sans" font-size="8.5" fill="#0f172a">{line}</text>')
        val='<b>'+escape(title)+'</b><br><br>'+'<br>'.join(lines)
        c=ET.SubElement(root,'mxCell',id=id,value=val,style=f'rounded=1;whiteSpace=wrap;html=1;fillColor={fill};strokeColor=#475569;fontSize=8.5;fontFamily=DejaVu Sans;spacing=5;verticalAlign=middle;',vertex='1',parent='1')
        ET.SubElement(c,'mxGeometry',x=str(x),y=str(y),width=str(w),height=str(h),**{'as':'geometry'})
    for i,(src,dst,pts,dashed) in enumerate(edges):
        d='M'+' L'.join(f'{x},{y}' for x,y in pts)
        svg.append(f'<path d="{d}" fill="none" stroke="#334155" stroke-width="0.9" marker-end="url(#arrow)"'+(' stroke-dasharray="3,2"' if dashed else '')+'/>')
        c=ET.SubElement(root,'mxCell',id=f'e{i}',value='',style='edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;endArrow=block;strokeWidth=0.9;'+('dashed=1;' if dashed else ''),edge='1',parent='1',source=src,target=dst)
        g=ET.SubElement(c,'mxGeometry',relative='1',**{'as':'geometry'}); ar=ET.SubElement(g,'Array',**{'as':'points'})
        for x,y in pts[1:-1]:ET.SubElement(ar,'mxPoint',x=str(x),y=str(y))
    for i,(x,y,text) in enumerate(notes):
        svg.append(f'<text x="{x}" y="{y}" text-anchor="middle" font-family="DejaVu Sans" font-size="8.5" fill="#334155">{escape(text)}</text>')
        c=ET.SubElement(root,'mxCell',id=f'n{i}',value=text,style='text;html=1;fontSize=8.5;fontFamily=DejaVu Sans;align=center;',vertex='1',parent='1'); ET.SubElement(c,'mxGeometry',x=str(x-100),y=str(y-10),width='200',height='15',**{'as':'geometry'})
    svg.append('</svg>'); P.joinpath(stem+'.svg').write_text('\n'.join(svg)); ET.indent(mx);ET.ElementTree(mx).write(P/(stem+'.drawio'),encoding='utf-8',xml_declaration=True)
    subprocess.run(['inkscape',str(P/(stem+'.svg')),'--export-type=pdf',f'--export-filename={P/(stem+".pdf")}'],check=True,capture_output=True)
    subprocess.run(['inkscape',str(P/(stem+'.svg')),'--export-type=png','--export-dpi=300',f'--export-filename={P/(stem+".png")}'],check=True,capture_output=True)

build('framework_architecture',516,150,[
 ('ledger',2,2,158,61,'Committed declaration',['IDs, releases, runtimes','GPUs, class, region','Records available at the gate'],'#e8f2fb'),
 ('risk',179,2,158,61,'Aggregate verification',['Workload-feasible projection','Total and daily-tail risk fit','Validation accuracy budget'],'#eef5e6'),
 ('runtime',356,2,158,61,'Indexed execution',['Contiguous runtime blocks','Capacity and energy checks','Recomputed risk residual'],'#fff2dc'),
 ('meter',2,87,158,61,'Independent meter',['Post-event execution ledger','Observed energy and timing','Scoring only; no event label'],'#f1f4f8'),
 ('cap',179,87,158,61,'Payment activation',['Frozen contract + closed meter','Payable reduction: their cap','Declaration replay is separate'],'#e8f5ef'),
 ('grid',356,87,158,61,'Signed grid value',['Same mapped workload profile','All finite N–1 contingencies','Value cap and participant shares'],'#f0eafa')],
 [('ledger','risk',[(160,32),(179,32)],False),('risk','runtime',[(337,32),(356,32)],False),('meter','cap',[(160,117),(179,117)],False),('risk','cap',[(258,63),(258,87)],False),('runtime','grid',[(435,63),(435,87)],False),('cap','grid',[(337,117),(356,117)],False)])

build('method_detail',252,199,[
 ('state',2,2,248,45,'1. Common feasible workload state',['Release • deadline • conservation • capacity','Cumulative service links declarations to power'],'#e8f2fb'),
 ('fit',2,62,248,45,'2. Validation-fitted aggregate verifier',['Seven-profile simplex; total + top-m tail budget','Accuracy bound relative to the causal anchor'],'#eef5e6'),
 ('execute',2,122,248,45,'3. Runtime blocks and composition test',['Recompute risk, accuracy, and payment-cap change','Pass a transported budget, or flag the gap'],'#fff2dc')],
 [('state','fit',[(126,47),(126,62)],False),('fit','execute',[(126,107),(126,122)],False)],
 notes=[(126,190,'Closed-meter payment remains a separate gate')])
# Stable filenames used by the manuscript and release inventory.
for src,dst in [('framework_architecture','fig0_framework'),('method_detail','fig_method_detail')]:
 for ext in ('pdf','png'):
  P.joinpath(dst+'.'+ext).write_bytes(P.joinpath(src+'.'+ext).read_bytes())
  P.joinpath(src+'.'+ext).unlink()
print('Editable vector diagrams rebuilt at native publication dimensions')
