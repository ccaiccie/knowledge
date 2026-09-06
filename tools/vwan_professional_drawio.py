from pathlib import Path
from xml.sax.saxutils import escape
OUT=Path('images/.generated_vwan_tmp')

def mxfile(name, nodes, edges, width=1600, height=900):
    cells=['<mxCell id="0"/>','<mxCell id="1" parent="0"/>']
    for i,n in enumerate(nodes, start=2):
        nid=n['id']; val=escape(n.get('label','')).replace('\n','&#xa;'); x,y,w,h=n['x'],n['y'],n['w'],n['h']; fill=n.get('fill','#FFFFFF'); stroke=n.get('stroke','#64748B'); fs=n.get('fs',14); rounded=n.get('rounded',1)
        style=f'rounded={rounded};whiteSpace=wrap;html=1;strokeWidth=2.5;fillColor={fill};strokeColor={stroke};fontSize={fs};fontFamily=Segoe UI;'
        cells.append(f'<mxCell id="{nid}" value="{val}" style="{style}" vertex="1" parent="1"><mxGeometry x="{x}" y="{y}" width="{w}" height="{h}" as="geometry"/></mxCell>')
    for j,e in enumerate(edges, start=100):
        color=e.get('color','#0078D4'); label=escape(e.get('label','')); src=e['src']; dst=e['dst']
        style=f'edgeStyle=orthogonalEdgeStyle;rounded=1;orthogonalLoop=1;jettySize=auto;html=1;strokeWidth=4;strokeColor={color};endArrow=block;endFill=1;endSize=16;fontSize=12;fontFamily=Segoe UI;'
        cells.append(f'<mxCell id="e{j}" value="{label}" style="{style}" edge="1" parent="1" source="{src}" target="{dst}"><mxGeometry relative="1" as="geometry"/></mxCell>')
    return f'<mxfile host="app.diagrams.net" modified="2026-09-06T03:30:00.000Z" agent="ChatGPT" version="24.7.17"><diagram id="{name}" name="Page-1"><mxGraphModel dx="1600" dy="900" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="{width}" pageHeight="{height}" math="0" shadow="0"><root>{"".join(cells)}</root></mxGraphModel></diagram></mxfile>'

def save(name,nodes,edges): (OUT/f'{name}.drawio').write_text(mxfile(name,nodes,edges))

nodes=[{'id':'spokes','label':'Spoke VNets\nVNet connections','x':70,'y':250,'w':210,'h':120,'fill':'#EAF6EA','stroke':'#107C10'},{'id':'branch','label':'Branches / On-prem\nVPN / ER / SD-WAN','x':70,'y':500,'w':210,'h':120,'fill':'#FFF3E0','stroke':'#D97706'},{'id':'router','label':'vHub Router\nroute association + propagation','x':390,'y':270,'w':220,'h':110,'fill':'#E8F3FC','stroke':'#0078D4'},{'id':'intent','label':'Routing Intent\nPrivate / Internet policies','x':690,'y':270,'w':220,'h':110,'fill':'#F0ECFF','stroke':'#6B4EFF'},{'id':'ngfw','label':'Integrated NGFW\nCheck Point / Fortinet / Cisco','x':690,'y':500,'w':220,'h':130,'fill':'#FDEBEC','stroke':'#D13438'},{'id':'dest','label':'Destination lookup\nspoke / branch / Internet','x':1010,'y':270,'w':200,'h':110,'fill':'#FFFFFF','stroke':'#7C3AED'}]
edges=[{'src':'spokes','dst':'router','label':'connected routes'},{'src':'branch','dst':'router','label':'learned routes'},{'src':'router','dst':'intent','label':'policy class'},{'src':'intent','dst':'ngfw','label':'service insertion'},{'src':'ngfw','dst':'dest','label':'inspected traffic'}]
save('architecture_v3',nodes,edges)

def east(forward=True):
 color='#0078D4' if forward else '#EA580C'; d='forward' if forward else 'return'; src=('Spoke A / VM-A\n10.10.1.4') if forward else ('Spoke B / VM-B\n10.20.1.4'); dst=('Spoke B / VM-B\n10.20.1.4') if forward else ('Spoke A / VM-A\n10.10.1.4')
 nodes=[{'id':'src','label':src,'x':115,'y':330,'w':250,'h':125,'fill':'#EAF6EA','stroke':'#107C10'},{'id':'lookup','label':'vHub route lookup\nclassify private traffic','x':560,'y':275,'w':220,'h':105,'fill':'#E8F3FC','stroke':'#0078D4'},{'id':'intent','label':'Routing Intent\nPrivate Traffic → NVA','x':820,'y':275,'w':220,'h':105,'fill':'#F0ECFF','stroke':'#6B4EFF'},{'id':'ngfw','label':'Integrated NGFW\nstateful inspection','x':690,'y':500,'w':220,'h':120,'fill':'#FDEBEC','stroke':'#D13438'},{'id':'dst','label':dst,'x':1235,'y':330,'w':250,'h':125,'fill':'#F3E8FF','stroke':'#7C3AED'}]
 edges=[{'src':'src','dst':'lookup','label':'1  VNet connection','color':color},{'src':'lookup','dst':'intent','label':'2  policy match','color':color},{'src':'intent','dst':'ngfw','label':'3  insert NVA','color':color},{'src':'ngfw','dst':'dst','label':'4  post-inspection route','color':color}]
 save(f'eastwest_{d}_v3',nodes,edges)

def branch(forward=True):
 color='#0078D4' if forward else '#EA580C'; d='forward' if forward else 'return'; nodes=[{'id':'branch','label':'Branch host\n10.50.1.25','x':95,'y':360,'w':225,'h':120,'fill':'#FFF3E0','stroke':'#D97706'},{'id':'gw','label':'VPN / ER Gateway\nbranch attachment','x':500,'y':270,'w':200,'h':110,'fill':'#E8F3FC','stroke':'#0078D4'},{'id':'router','label':'vHub Router\nlearned branch/spoke routes','x':760,'y':270,'w':200,'h':110,'fill':'#E8F3FC','stroke':'#0078D4'},{'id':'ngfw','label':'Integrated NGFW\nbranch↔Azure policy/state','x':760,'y':510,'w':200,'h':120,'fill':'#FDEBEC','stroke':'#D13438'},{'id':'vm','label':'VM-A\n10.10.1.4','x':1275,'y':360,'w':225,'h':120,'fill':'#EAF6EA','stroke':'#107C10'}]
 seq=[('branch','gw','1  IPsec / ER'),('gw','router','2  route enters hub'),('router','ngfw','3  Private Traffic policy'),('ngfw','vm','4  spoke lookup')] if forward else [('vm','ngfw','1  VNet connection'),('ngfw','router','2  Private Traffic policy'),('router','gw','3  branch route lookup'),('gw','branch','4  VPN / ER egress')]
 save(f'branch_{d}_v3',nodes,[{'src':a,'dst':b,'label':c,'color':color} for a,b,c in seq])

def internet(forward=True):
 color='#0078D4' if forward else '#EA580C'; d='forward' if forward else 'return'; nodes=[{'id':'vm','label':'VM-A\n10.10.1.4:51514','x':100,'y':365,'w':240,'h':115,'fill':'#EAF6EA','stroke':'#107C10'},{'id':'default','label':'Secured default route\n0.0.0.0/0 → NVA','x':515,'y':265,'w':220,'h':105,'fill':'#E8F3FC','stroke':'#0078D4'},{'id':'intent','label':'Routing Intent\nInternet Traffic → NVA','x':815,'y':265,'w':220,'h':105,'fill':'#F0ECFF','stroke':'#6B4EFF'},{'id':'ngfw','label':'Integrated NGFW\npolicy + NAT + state','x':665,'y':510,'w':230,'h':125,'fill':'#FDEBEC','stroke':'#D13438'},{'id':'nat','label':'NAT transformation\n10.10.1.4:51514 ⇄ public-SNAT:port','x':930,'y':505,'w':190,'h':135,'fill':'#FFFFFF','stroke':'#F59E0B'},{'id':'srv','label':'Internet server\n8.8.8.8:443','x':1270,'y':365,'w':230,'h':115,'fill':'#FFF3E0','stroke':'#D97706'}]
 seq=[('vm','default','1  default route'),('default','intent','2  Internet class'),('intent','ngfw','3  insert NGFW'),('ngfw','srv','4  SNAT then egress')] if forward else [('srv','ngfw','1  response to SNAT IP'),('ngfw','intent','2  state + reverse NAT'),('intent','default','3  private route lookup'),('default','vm','4  VNet connection')]
 save(f'internet_{d}_v3',nodes,[{'src':a,'dst':b,'label':c,'color':color} for a,b,c in seq])

def dnat(forward=True):
 color='#0078D4' if forward else '#EA580C'; d='forward' if forward else 'return'; nodes=[{'id':'client','label':'Internet client\n203.0.113.25:51514','x':90,'y':365,'w':230,'h':115,'fill':'#FFF3E0','stroke':'#D97706'},{'id':'pip','label':'Standard Public IP\n198.51.100.40:443','x':475,'y':250,'w':210,'h':110,'fill':'#E8F3FC','stroke':'#0078D4'},{'id':'lb','label':'Azure inbound LB\n5-tuple → healthy NVA','x':745,'y':250,'w':210,'h':110,'fill':'#E8F3FC','stroke':'#0078D4'},{'id':'ngfw','label':'Integrated NGFW\nDNAT + usually SNAT','x':745,'y':505,'w':210,'h':125,'fill':'#FDEBEC','stroke':'#D13438'},{'id':'nat','label':'NAT at NGFW\ndst 198.51.100.40:443 → 10.60.0.4:443\nSNAT typically added','x':980,'y':500,'w':180,'h':145,'fill':'#FFFFFF','stroke':'#F59E0B'},{'id':'backend','label':'Backend\n10.60.0.4:443','x':1280,'y':365,'w':230,'h':115,'fill':'#EAF6EA','stroke':'#107C10'}]
 seq=[('client','pip','1  to published IP'),('pip','lb','2  frontend flow'),('lb','ngfw','3  healthy NVA'),('ngfw','backend','4  translated flow')] if forward else [('backend','ngfw','1  reply to SNAT source'),('ngfw','lb','2  reverse DNAT/SNAT'),('lb','pip','3  same selected flow'),('pip','client','4  from public IP')]
 save(f'dnat_{d}_v3',nodes,[{'src':a,'dst':b,'label':c,'color':color} for a,b,c in seq])

for f in [True,False]: east(f); branch(f); internet(f); dnat(f)
print('drawio generated',len(list(OUT.glob('*_v3.drawio'))))