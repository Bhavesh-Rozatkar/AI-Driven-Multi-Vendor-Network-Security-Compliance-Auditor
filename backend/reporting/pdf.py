from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
def build_pdf(result):
 b=BytesIO();doc=SimpleDocTemplate(b,pagesize=A4,rightMargin=30,leftMargin=30,topMargin=30,bottomMargin=30);s=getSampleStyleSheet();story=[Paragraph("Network Compliance & Remediation Report",s["Title"]),Spacer(1,10)];d=result.get("device",{});story.append(Paragraph(f"Device: {d.get('vendor')} {d.get('device_type')} — {d.get('host','')}",s["BodyText"]));c=result.get("compliance",{});rows=[["Control","Status","Evidence"]]+[[x.get("rule_id"),x.get("status"),Paragraph(str(x.get("evidence") or x.get("reason") or ""),s["BodyText"])] for x in c.get("results",[])];t=Table(rows,colWidths=[70,80,360],repeatRows=1);t.setStyle(TableStyle([("GRID",(0,0),(-1,-1),.3,colors.grey),("BACKGROUND",(0,0),(-1,0),colors.lightgrey)]));story += [t,Spacer(1,10),Paragraph("Verification",s["Heading2"]),Paragraph(str(result.get("verification",{}).get("status","")),s["BodyText"])];doc.build(story);b.seek(0);return b.getvalue()
