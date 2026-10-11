import json
from pathlib import Path

p=Path('tp_template.ipynb')
n=json.loads(p.read_text(encoding='utf-8'))
for c in n['cells']:
    s=''.join(c['source'])
    s=s.replace('SUM(n.consultas_prenatal_codigo BETWEEN 0 AND 90) AS respostas_validas',
                'SUM(CASE WHEN n.consultas_prenatal_codigo BETWEEN 0 AND 90 THEN 1 ELSE 0 END) AS respostas_validas')
    s=s.replace('SUM(n.consultas_prenatal_codigo BETWEEN 0 AND 90)/COUNT(*)',
                'SUM(CASE WHEN n.consultas_prenatal_codigo BETWEEN 0 AND 90 THEN 1 ELSE 0 END)/COUNT(*)')
    s=s.replace('SUM(n.consultas_prenatal_codigo BETWEEN 0 AND 90) AS n_validos',
                'SUM(CASE WHEN n.consultas_prenatal_codigo BETWEEN 0 AND 90 THEN 1 ELSE 0 END) AS n_validos')
    s=s.replace('País, Levantamento, Domicílio, Mulher, Nascimento e Método atendem',
                'Levantamento, Domicílio, Mulher, Nascimento, Criança e Método atendem')
    s=s.replace('| Pais, Levantamento, Domicilio, Mulher, Nascimento, Metodo |',
                '| Levantamento, Domicilio, Mulher, Nascimento, Crianca, Metodo |')
    if c['cell_type']=='markdown' and s.startswith('# 6. Consultas'):
        s+='\n\nAs consultas 3, 5, 6 e 7 usam contagens ou proporções amostrais não ponderadas; 4, 8, 9 e 10 utilizam pesos. Quintis de riqueza são posições relativas dentro de cada país: o quintil mais pobre de dois países não implica a mesma renda ou privação absoluta. Escolaridade e riqueza também não controlam idade, estado conjugal, preferências reprodutivas ou acesso aos serviços.\n'
    c['source']=s.splitlines(True)

sensitivity='''# Sensibilidade: verificar inversões com mais respostas por estrato.
sensibilidade=[]
for minimo in [30,50,100]:
    for (codigo,nome),g in r9.groupby(['codigo','nome']):
        numeros=g.pivot(index=['riqueza','escolaridade'],columns='residencia',values='n')
        suporte=numeros.index[(numeros.get(1,0)>=minimo)&(numeros.get(2,0)>=minimo)]
        if len(suporte)==0: continue
        sub=g.set_index(['riqueza','escolaridade']).loc[suporte].reset_index()
        wt=sub.pivot(index=['riqueza','escolaridade'],columns='residencia',values='peso_total')
        uso=sub.pivot(index=['riqueza','escolaridade'],columns='residencia',values='peso_uso')
        padrao=(wt[1]+wt[2]); padrao=padrao/padrao.sum()
        bruta=100*(uso[1].sum()/wt[1].sum()-uso[2].sum()/wt[2].sum())
        ajustada=100*((uso[1]/wt[1]-uso[2]/wt[2])*padrao).sum()
        sensibilidade.append([codigo,nome,minimo,len(suporte),bruta,ajustada,bruta*ajustada<0])
sensibilidade=pd.DataFrame(sensibilidade,columns=['codigo','pais','minimo_por_area','estratos','bruta_pp','padronizada_pp','inversao'])
display(sensibilidade.groupby('minimo_por_area').agg(paises=('codigo','nunique'),inversoes=('inversao','sum')))
display(sensibilidade[sensibilidade.codigo.isin(ajustes.loc[ajustes.inversao,'codigo'])].round(2))
persistentes=sensibilidade.groupby('pais').filter(lambda g: len(g)==3 and g.inversao.all()).pais.unique()
display(Markdown('**Robustez descritiva:** a inversão permaneceu nos três limiares em '+(', '.join(sorted(persistentes)) or 'nenhum país')+'. Mudar o limiar também muda o suporte comum; esse exercício verifica sensibilidade, não significância estatística. A amostra ajustada não representa os estratos excluídos.'))
'''
for i,c in enumerate(n['cells']):
    if c['cell_type']=='code' and ''.join(c['source']).startswith('ajustes=[]'):
        n['cells'].insert(i+1,{'cell_type':'code','metadata':{},'source':sensitivity.splitlines(True),'execution_count':None,'outputs':[]})
        break

# Validate/exercise all ten query results and every country in the final artifact.
verification='''assert set(cobertura.codigo)==set(conn.execute('SELECT codigo FROM Pais').fetchall()[i][0] for i in range(37))
for numero in range(1,11):
    tabela=globals()[f'r{numero}']
    assert len(tabela)>0, f'Consulta {numero} deve retornar dados.'
    coluna='pais_codigo' if numero<=5 else 'codigo'
    assert tabela[coluna].nunique()>1, f'Consulta {numero} deve abranger vários países.'
assert r3.pais_codigo.nunique()==37
assert len(ajustes)>1 and len(prenatal)>1
print('Dez consultas validadas, comparação nacional de 37 países e análises ajustadas com cobertura explícita.')
'''
for i,c in enumerate(n['cells']):
    if c['cell_type']=='code' and ''.join(c['source']).startswith('conn.close()'):
        n['cells'].insert(i,{'cell_type':'code','metadata':{},'source':verification.splitlines(True),'execution_count':None,'outputs':[]})
        break
for i,c in enumerate(n['cells']):
    c['id']=f'dhs-normalizado-{i:03d}'
    if c['cell_type']=='code':
        compile(''.join(c['source']),f'cell_{i}','exec')
        c['outputs']=[]; c['execution_count']=None
p.write_text(json.dumps(n,ensure_ascii=False,indent=1)+'\n',encoding='utf-8')

import nbformat
from nbclient import NotebookClient
notebook=nbformat.read(p,as_version=4)
nbformat.validate(notebook)
def report(cell_index,**kwargs):
    print(f'Jupyter cell {cell_index}',flush=True)
client=NotebookClient(notebook,timeout=900,kernel_name='python3',resources={'metadata':{'path':str(p.resolve().parent)}},on_cell_start=report)
client.execute()
nbformat.validate(notebook)
nbformat.write(notebook,p)
print('Execução real Jupyter e validação nbformat concluídas.',flush=True)
