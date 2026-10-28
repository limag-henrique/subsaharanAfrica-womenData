import base64,html,json,re
from pathlib import Path
from markdown_it import MarkdownIt
root=Path.cwd()
n=json.loads((root/'Saúde da Mulher na África Subsaariana.ipynb').read_text(encoding='utf-8'))
md=MarkdownIt('commonmark',{'html':True}).enable('table')
css='''@page {size:A4;margin:17mm 14mm 18mm} *{box-sizing:border-box} body{font-family:Arial,sans-serif;color:#222;font-size:10pt;line-height:1.45;margin:0} h1{font-size:20pt;margin:20pt 0 12pt;break-after:avoid} h2{font-size:15pt;break-after:avoid} h3{font-size:12pt;break-after:avoid} p,li{orphans:3;widows:3} a{color:#18568c;overflow-wrap:anywhere} img{max-width:100%;height:auto;display:block;margin:12px auto;max-height:235mm;object-fit:contain} p:has(>img){break-inside:avoid} pre{font-family:Consolas,monospace;font-size:7.7pt;line-height:1.3;white-space:pre-wrap;overflow-wrap:anywhere;word-break:break-word;border:1px solid #ddd;background:#f7f7f7;padding:8px} code{font-family:Consolas,monospace;font-size:0.9em} table{border-collapse:collapse;max-width:100%;width:100%;font-size:7.5pt;table-layout:auto;margin:10pt 0} th,td{border:1px solid #ddd;padding:3px;overflow-wrap:anywhere} tr{break-inside:avoid} thead{display:table-header-group} .output{margin:8px 0 18px} .diagram{break-before:page;break-after:page} .diagram h1{margin-top:0} .diagram img{max-height:235mm} .cell{margin-bottom:12px} .prompt{font-size:8pt;color:#666;margin-bottom:3px}'''
parts=['<!doctype html><html lang="pt-BR"><meta charset="utf-8"><title>Saúde da Mulher na África Subsaariana</title><style>'+css+'</style><body>']
for c in n['cells']:
 source=''.join(c.get('source',[]))
 if c['cell_type']=='markdown':
  for name,data in c.get('attachments',{}).items():
   mime=next(iter(data)); raw=data[mime]; raw=''.join(raw) if isinstance(raw,list) else raw
   source=source.replace('attachment:'+name,'data:'+mime+';base64,'+raw)
  if source.startswith('# 4. Diagrama ER') or source.startswith('# 5. Diagrama relacional'):
   lines=source.splitlines(); index=next(i for i,l in enumerate(lines) if l.startswith('!['))
   parts.append('<section class="diagram">'+md.render('\n'.join(lines[:index+1]))+'</section>')
   parts.append(md.render('\n'.join(lines[index+1:])))
  else: parts.append('<section class="cell">'+md.render(source)+'</section>')
 elif c['cell_type']=='code':
  parts.append('<section class="cell"><div class="prompt">Código</div><pre>'+html.escape(source)+'</pre>')
  for o in c.get('outputs',[]):
   data=o.get('data',{})
   if 'image/png' in data:
    raw=data['image/png']; raw=''.join(raw) if isinstance(raw,list) else raw
    parts.append('<div class="output"><img src="data:image/png;base64,'+raw+'"></div>')
   elif 'text/html' in data: parts.append('<div class="output">'+''.join(data['text/html'])+'</div>')
   elif 'text' in o: parts.append('<pre class="output">'+html.escape(''.join(o['text']))+'</pre>')
   elif 'text/plain' in data: parts.append('<pre class="output">'+html.escape(''.join(data['text/plain']))+'</pre>')
   elif o.get('output_type')=='error': parts.append('<pre>'+html.escape('\n'.join(o.get('traceback',[])))+'</pre>')
  parts.append('</section>')
parts.append('</body></html>')
(root/'tmp/pdfs/notebook.html').write_text('\n'.join(parts),encoding='utf-8')
print('HTML gerado com código, saídas e imagens incorporadas.')
