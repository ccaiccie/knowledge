from pathlib import Path
from xml.sax.saxutils import escape
OUT=Path('images'); OUT.mkdir(parents=True,exist_ok=True)
W,H=1500,760
C={'bg':'#FAFBFD','text':'#0F172A','muted':'#64748B','azure':'#0078D4','azure_fill':'#EEF7FD','route':'#6554C0','route_fill':'#F3F0FF','sec':'#C2413B','sec_fill':'#FFF0EF','green':'#15803D','green_fill':'#F0FDF4','orange':'#C66A15','orange_fill':'#FFF7ED','purple':'#7E22CE','purple_fill':'#FAF5FF','border':'#CBD5E1','return':'#D97706'}

def esc(s): return escape(str(s))

def node(id,x,y,w,h,title,sub='',kind='azure'):
    fill=C.get(kind+'_fill','#fff'); stroke=C.get(kind,C['border'])
    return {'id':id,'x':x,'y':y,'w':w,'h':h,'title':title,'sub':sub,'fill':fill,'stroke':stroke}

def edge(a,b,n,label='',points=None): return {'a':a,'b':b,'n':n,'label':label,'points':points}

def centers(n): return n['x']+n['w']/2,n['y']+n['h']/2

def attach(a,b):
    ax,ay=centers(a); bx,by=centers(b); dx,dy=bx-ax,by-ay
    if abs(dx)>=abs(dy):
        x1=a['x']+a['w'] if dx>0 else a['x']; y1=ay; x2=b['x'] if dx>0 else b['x']+b['w']; y2=by
    else:
        x1=ax; y1=a['y']+a['h'] if dy>0 else a['y']; x2=bx; y2=b['y'] if dy>0 else b['y']+b['h']
    return x1,y1,x2,y2

def svg(name,title,subtitle,nodes,edges,direction='forward',note=None,regions=None):
    color=C['azure'] if direction=='forward' else C['return']
    marker='arr'
    s=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
       f'<defs><marker id="{marker}" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto"><path d="M0,0 L0,8 L8,4 z" fill="{color}"/></marker></defs>',
       f'<rect width="100%" height="100%" fill="{C["bg"]}"/>',
       f'<text x="54" y="56" font-family="Segoe UI,Arial" font-size="28" font-weight="700" fill="{C["text"]}">{esc(title)}</text>',
       f'<text x="54" y="86" font-family="Segoe UI,Arial" font-size="15" fill="{C["muted"]}">{esc(subtitle)}</text>']
    if regions:
        for r in regions:
            s.append(f'<rect x="{r[0]}" y="{r[1]}" width="{r[2]}" height="{r[3]}" rx="22" fill="{r[5]}" stroke="{r[6]}" stroke-width="1.5"/>')
            s.append(f'<text x="{r[0]+18}" y="{r[1]+28}" font-family="Segoe UI,Arial" font-size="12" font-weight="700" fill="{r[6]}">{esc(r[4])}</text>')
    nd={n['id']:n for n in nodes}
    for e in edges:
        a,b=nd[e['a']],nd[e['b']]; x1,y1,x2,y2=attach(a,b)
        if e.get('points'):
            pts=[(x1,y1)]+e['points']+[(x2,y2)]
            p=' '.join(f'{x},{y}' for x,y in pts)
            s.append(f'<polyline points="{p}" fill="none" stroke="{color}" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" marker-end="url(#{marker})"/>')
            mx,my=pts[len(pts)//2]
        else:
            s.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="2.5" stroke-linecap="round" marker-end="url(#{marker})"/>')
            mx,my=(x1+x2)/2,(y1+y2)/2
        s.append(f'<circle cx="{mx}" cy="{my}" r="9" fill="#fff" stroke="{color}" stroke-width="1.6"/><text x="{mx}" y="{my+3.5}" text-anchor="middle" font-family="Segoe UI,Arial" font-size="9" font-weight="700" fill="{color}">{e["n"]}</text>')
        if e.get('label'):
            s.append(f'<text x="{mx}" y="{my-14}" text-anchor="middle" font-family="Segoe UI,Arial" font-size="10.5" font-weight="600" fill="{C["muted"]}" style="paint-order:stroke;stroke:{C["bg"]};stroke-width:4px">{esc(e["label"])}</text>')
    for n in nodes:
        s.append(f'<rect x="{n["x"]}" y="{n["y"]}" width="{n["w"]}" height="{n["h"]}" rx="14" fill="{n["fill"]}" stroke="{n["stroke"]}" stroke-width="1.8"/>')
        s.append(f'<text x="{n["x"]+n["w"]/2}" y="{n["y"]+n["h"]/2-5}" text-anchor="middle" font-family="Segoe UI,Arial" font-size="16" font-weight="700" fill="{C["text"]}">{esc(n["title"])}</text>')
        if n['sub']:
            s.append(f'<text x="{n["x"]+n["w"]/2}" y="{n["y"]+n["h"]/2+20}" text-anchor="middle" font-family="Segoe UI,Arial" font-size="11.5" fill="{C["muted"]}">{esc(n["sub"])}</text>')
    if note:
        s.append(f'<text x="54" y="724" font-family="Segoe UI,Arial" font-size="12.5" font-weight="600" fill="{C["muted"]}">{esc(note)}</text>')
    s.append('</svg>')
    (OUT/f'{name}.svg').write_text(''.join(s))
    drawio(name,nodes,edges,color,regions)

def drawio(name,nodes,edges,color,regions=None):
    cells=['<mxCell id="0"/>','<mxCell id="1" parent="0"/>']
    if regions:
        for i,r in enumerate(regions,10):
            val=esc(r[4]); style=f'rounded=1;whiteSpace=wrap;html=1;fillColor={r[5]};strokeColor={r[6]};strokeWidth=1.5;fontSize=12;fontStyle=1;verticalAlign=top;align=left;spacingTop=8;spacingLeft=8;'
            cells.append(f'<mxCell id="r{i}" value="{val}" style="{style}" vertex="1" parent="1"><mxGeometry x="{r[0]}" y="{r[1]}" width="{r[2]}" height="{r[3]}" as="geometry"/></mxCell>')
    for n in nodes:
        val=esc(n['title'] + ('\n'+n['sub'] if n['sub'] else '')).replace('\n','&#xa;')
        style=f'rounded=1;whiteSpace=wrap;html=1;fillColor={n["fill"]};strokeColor={n["stroke"]};strokeWidth=1.8;fontSize=14;fontFamily=Segoe UI;'
        cells.append(f'<mxCell id="{n["id"]}" value="{val}" style="{style}" vertex="1" parent="1"><mxGeometry x="{n["x"]}" y="{n["y"]}" width="{n["w"]}" height="{n["h"]}" as="geometry"/></mxCell>')
    for i,e in enumerate(edges,100):
        val=esc(f'{e["n"]}  {e.get("label","")}')
        style=f'edgeStyle=orthogonalEdgeStyle;rounded=1;orthogonalLoop=1;jettySize=auto;html=1;strokeWidth=2.5;strokeColor={color};endArrow=block;endFill=1;endSize=8;fontSize=10;fontColor={C["muted"]};fontFamily=Segoe UI;'
        cells.append(f'<mxCell id="e{i}" value="{val}" style="{style}" edge="1" parent="1" source="{e["a"]}" target="{e["b"]}"><mxGeometry relative="1" as="geometry"/></mxCell>')
    xml=f'<mxfile host="app.diagrams.net" modified="2026-09-06T04:00:00.000Z" agent="ChatGPT"><diagram id="{name}" name="Page-1"><mxGraphModel page="1" pageScale="1" pageWidth="{W}" pageHeight="{H}"><root>{"".join(cells)}</root></mxGraphModel></diagram></mxfile>'
    (OUT/f'{name}.drawio').write_text(xml)

HUB=(430,145,640,500,'AZURE VIRTUAL WAN HUB','#F5FAFE','#7CBDE8')

def build():
    nodes=[node('spokes',70,240,220,90,'Spoke VNets','VNet connections','green'),node('branches',70,455,220,90,'Branches / On-prem','VPN • ER • SD-WAN','orange'),node('router',500,235,200,90,'vHub Router','managed routing fabric'),node('intent',775,235,200,90,'Routing Intent','Private / Internet policy','route'),node('ngfw',775,445,200,100,'Integrated NGFW','qualified third-party NVA','sec'),node('dest',1150,335,220,90,'Destination','spoke • branch • Internet','purple')]
    edges=[edge('spokes','router',1,'connected routes'),edge('branches','router',2,'learned routes'),edge('router','intent',3,'classify'),edge('intent','ngfw',4,'service insert'),edge('ngfw','dest',5,'final lookup')]
    svg('architecture_v5','Integrated NGFW inside an Azure Virtual WAN hub','Ownership and service-insertion model; forwarding details are intentionally abstracted.',nodes,edges,'forward','Routing Intent selects the security next hop; the vHub remains the managed transit routing fabric.',[HUB])

    nodes=[node('sources',80,250,230,100,'Route sources','spokes • VPN • ER','green'),node('routes',470,220,210,95,'vHub routes','association + propagation'),node('intent',760,220,210,95,'Routing Intent','traffic-class policy','route'),node('ngfw',760,430,210,100,'Integrated NGFW','security next hop','sec'),node('final',1130,325,230,100,'Final route lookup','destination connection','purple')]
    edges=[edge('sources','routes',1,'learn'),edge('routes','intent',2,'classify'),edge('intent','ngfw',3,'steer'),edge('ngfw','final',4,'return inspected flow')]
    svg('routing_intent_v5','Routing Intent — control-plane view','How learned routes and policy classification create service insertion.',nodes,edges,'forward','This is not a per-spoke UDR rewrite; Virtual WAN programs the hub/connection routing behavior.',[HUB])

    for ret in (False,True):
        d='return' if ret else 'forward'; direction='return' if ret else 'forward'
        left=('VM-B','10.20.1.4','purple') if ret else ('VM-A','10.10.1.4','green'); right=('VM-A','10.10.1.4','green') if ret else ('VM-B','10.20.1.4','purple')
        nodes=[node('src',90,320,210,90,left[0],left[1],left[2]),node('lookup',490,235,200,90,'vHub lookup','Private Traffic'),node('intent',760,235,200,90,'Routing Intent','→ Integrated NGFW','route'),node('ngfw',625,445,200,100,'Integrated NGFW','stateful inspection','sec'),node('dst',1190,320,210,90,right[0],right[1],right[2])]
        edges=[edge('src','lookup',1,'VNet connection'),edge('lookup','intent',2,'private class'),edge('intent','ngfw',3,'service insert'),edge('ngfw','dst',4,'destination route')]
        note='Forward: session state is created; source IP normally remains unchanged.' if not ret else 'Return: existing/synchronized firewall state must be matched before the spoke lookup.'
        svg(f'eastwest_{d}_v5',f'East-west {d} path',f'{left[0]} → {right[0]}; one direction per diagram.',nodes,edges,direction,note,[HUB])

    for ret in (False,True):
        d='return' if ret else 'forward'; direction='return' if ret else 'forward'
        nodes=[node('branch',70,335,210,90,'Branch host','10.50.1.25','orange'),node('gw',455,240,190,90,'VPN / ER Gateway','branch attachment'),node('router',725,240,190,90,'vHub Router','route lookup'),node('ngfw',725,445,190,100,'Integrated NGFW','policy + state','sec'),node('vm',1200,335,210,90,'VM-A','10.10.1.4','green')]
        if ret: edges=[edge('vm','ngfw',1,'VNet connection'),edge('ngfw','router',2,'stateful return'),edge('router','gw',3,'branch route'),edge('gw','branch',4,'VPN / ER')]
        else: edges=[edge('branch','gw',1,'VPN / ER'),edge('gw','router',2,'learned route'),edge('router','ngfw',3,'Private policy'),edge('ngfw','vm',4,'spoke route')]
        note='Verify branch route learning at the gateway separately from firewall policy.' if not ret else 'Verify 10.50.0.0/16 resolves back to the intended VPN/ER connection after firewall state processing.'
        svg(f'branch_{d}_v5',f'Branch-to-spoke {d} path','Gateway attachment, security insertion, and spoke routing shown as separate stages.',nodes,edges,direction,note,[HUB])

    for ret in (False,True):
        d='return' if ret else 'forward'; direction='return' if ret else 'forward'
        nodes=[node('vm',70,335,210,90,'VM-A','10.10.1.4:51514','green'),node('default',450,235,200,90,'Secured default','0.0.0.0/0 → NVA'),node('intent',725,235,200,90,'Routing Intent','Internet Traffic','route'),node('ngfw',725,445,200,105,'Integrated NGFW','policy • state • SNAT','sec'),node('internet',1200,335,210,90,'Internet server','8.8.8.8:443','orange')]
        if ret: edges=[edge('internet','ngfw',1,'reply to SNAT IP'),edge('ngfw','intent',2,'reverse NAT'),edge('intent','default',3,'private lookup'),edge('default','vm',4,'VNet connection')]
        else: edges=[edge('vm','default',1,'default route'),edge('default','intent',2,'Internet class'),edge('intent','ngfw',3,'service insert'),edge('ngfw','internet',4,'SNAT + egress')]
        note='NAT occurs at the NGFW: 10.10.1.4:51514 ↔ vendor/public translated source.' if not ret else 'Reverse NAT restores the private client before the vHub resolves the spoke route.'
        svg(f'internet_{d}_v5',f'Internet egress {d} path','The secured default route and NAT point are the two operational checkpoints.',nodes,edges,direction,note,[HUB])

    for ret in (False,True):
        d='return' if ret else 'forward'; direction='return' if ret else 'forward'
        nodes=[node('client',55,335,210,90,'Internet client','203.0.113.25:51514','orange'),node('pip',400,220,190,90,'Standard Public IP','198.51.100.40:443'),node('lb',655,220,190,90,'Azure inbound LB','healthy NVA selection'),node('ngfw',655,445,190,105,'Integrated NGFW','DNAT + usually SNAT','sec'),node('backend',1205,335,210,90,'Backend','10.60.0.4:443','green')]
        if ret: edges=[edge('backend','ngfw',1,'reply to SNAT source'),edge('ngfw','lb',2,'reverse NAT'),edge('lb','pip',3,'selected flow'),edge('pip','client',4,'public response')]
        else: edges=[edge('client','pip',1,'published IP'),edge('pip','lb',2,'frontend flow'),edge('lb','ngfw',3,'healthy NVA'),edge('ngfw','backend',4,'translated flow')]
        note='Forward translation: dst 198.51.100.40:443 → 10.60.0.4:443; SNAT is commonly added for symmetry.' if not ret else 'Return traffic reverses the NGFW translation before Azure sends the response from the published public IP.'
        svg(f'dnat_{d}_v5',f'Internet inbound DNAT {d} path','Public frontend, platform load balancing, firewall NAT, and backend routing are distinct stages.',nodes,edges,direction,note,[HUB])

build()
print('generated',len(list(OUT.glob('*_v5.svg'))),'SVG and',len(list(OUT.glob('*_v5.drawio'))),'drawio files')
