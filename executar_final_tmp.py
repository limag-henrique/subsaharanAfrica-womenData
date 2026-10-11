from pathlib import Path
import json
import nbformat
from nbclient import NotebookClient

p=Path('tp_template.ipynb')
n=nbformat.read(p,as_version=4)
images=json.loads(Path('diagramas_corrigidos_tmp.json').read_text(encoding='utf-8'))
by_name={next(iter(c['attachments'])):c['attachments'] for c in images}
for c in n.cells:
    if c.get('attachments'):
        name=next(iter(c.attachments))
        c.attachments=by_name[name]
    if c.cell_type=='code':
        c.source=c.source.replace('assert set(cobertura.codigo)==set(conn.execute(\'SELECT codigo FROM Pais\').fetchall()[i][0] for i in range(37))',
                                  "assert set(cobertura.codigo)=={r[0] for r in conn.execute('SELECT codigo FROM Pais')}")
        c.source=c.source.replace('assert r3.pais_codigo.nunique()==37',
                                  "assert set(r3.pais_codigo)==set(cobertura.codigo)-{'SD'}, 'Sudão não possui residência disponível neste recorte.'")
    if c.cell_type=='markdown' and c.source.startswith('# 6. Consultas'):
        c.source+='\n\n**Cobertura dos cruzamentos:** o Sudão tem mulheres no inventário, mas residência e riqueza ausentes em IR e nenhum HR selecionado. Ele permanece na cobertura dos 37 países; não entra nas estratificações rural–urbano/riqueza. Outros países também podem faltar em indicadores específicos por ausência de resposta ou suporte comum. Exclusão analítica é informada, não convertida em zero.\n'
nbformat.validate(n)
nbformat.write(n,p)
def report(cell_index,**kwargs): print(f'Jupyter cell {cell_index}',flush=True)
try:
    NotebookClient(n,timeout=900,kernel_name='python3',resources={'metadata':{'path':str(p.resolve().parent)}},on_cell_start=report).execute()
finally:
    nbformat.write(n,p)
nbformat.validate(n)
print('Notebook completo executado em Jupyter, validado e salvo.',flush=True)
