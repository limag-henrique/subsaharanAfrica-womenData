"""Exporta o relatório executado e os diagramas para leitura e impressão."""
from pathlib import Path
import nbformat
from bs4 import BeautifulSoup
from nbconvert import HTMLExporter
from playwright.sync_api import sync_playwright, Error

RAIZ = Path(__file__).resolve().parents[1]


def main():
    saida = RAIZ / 'output/pdf'
    saida.mkdir(parents=True, exist_ok=True)
    notebook = nbformat.read(RAIZ / 'Saúde da Mulher na África Subsaariana.ipynb', as_version=4)
    assert all(c.get('execution_count') is not None for c in notebook.cells if c.cell_type == 'code'), 'Execute o notebook antes de exportar.'
    assert not any(o.output_type == 'error' for c in notebook.cells for o in c.get('outputs', []))
    with sync_playwright() as p:
        try:
            navegador = p.chromium.launch(channel='msedge', headless=True)
        except Error:
            navegador = p.chromium.launch(headless=True)
        pagina = navegador.new_page(device_scale_factor=2)
        for nome in ['Diagrama Relacional']:
            svg = RAIZ / 'docs' / f'{nome}.svg'
            pagina.goto(svg.as_uri())
            pagina.locator('svg').screenshot(path=str(svg.with_suffix('.png')))
        exportador = HTMLExporter(exclude_input=True, exclude_input_prompt=True, exclude_output_prompt=True)
        html, _ = exportador.from_notebook_node(notebook)
        documento = BeautifulSoup(html, 'html.parser')
        base = documento.new_tag('base', href=RAIZ.as_uri() + '/')
        documento.head.insert(0, base)
        for detalhe in documento.select('details'):
            detalhe['open'] = ''
            linhas = detalhe.select('tbody tr')
            if len(linhas) > 30:
                for linha in linhas[12:]:
                    linha.decompose()
                nota = documento.new_tag('p')
                nota.string = f'Amostra de 12 das {len(linhas)} linhas; tabela integral no notebook.'
                detalhe.append(nota)
        for cabecalho in documento.select('th'):
            if cabecalho.string:
                cabecalho.string = cabecalho.string.replace('_', ' ')
        for imagem in documento.select('img'):
            rotulo = imagem.get('alt', '').lower()
            if 'diagrama' in rotulo or 'Diagrama' in imagem.get('src', ''):
                if 'relacional' in rotulo or 'Relacional' in imagem['src']:
                    imagem['src'] = (RAIZ / 'docs/Diagrama Relacional.svg').as_uri()
                paragrafo = imagem.parent
                titulo = paragrafo.find_previous_sibling('h1')
                legenda = paragrafo.find_next_sibling('p')
                bloco = documento.new_tag('div', attrs={'class': 'pagina-diagrama'})
                paragrafo.insert_before(bloco)
                if titulo:
                    bloco.append(titulo.extract())
                bloco.append(paragrafo.extract())
                if legenda:
                    bloco.append(legenda.extract())
        estilo = documento.new_tag('style')
        estilo.string = '''
@page { size: A4; margin: 14mm; }
@page diagrama { size: A3; margin: 15mm; }
body { font-family: Arial, sans-serif; color: #18262d; }
.jp-Notebook { padding: 0; }
.jp-Cell { padding: 4px 0; }
.jp-InputPrompt, .jp-OutputPrompt { display: none; }
.jp-OutputArea-output { overflow: visible !important; max-height: none !important; }
h1, h2, h3, summary { break-after: avoid; break-inside: avoid; }
p, li { orphans: 3; widows: 3; font-size: 9.5pt; line-height: 1.3; }
pre { white-space: pre-wrap !important; overflow-wrap: anywhere; font-size: 8pt; line-height: 1.2 !important; break-inside: avoid; }
table { border-collapse: collapse; width: 100%; font-size: 7.5pt !important; }
th, td { padding: 3px 4px !important; overflow-wrap: anywhere; }
thead { display: table-header-group; }
tr { break-inside: avoid; }
img { max-width: 100%; height: auto; }
.jp-RenderedImage { break-inside: avoid; }
.jp-RenderedImage img { max-height: 235mm; object-fit: contain; }
.pagina-diagrama { page: diagrama; break-before: page; break-after: page;
    break-inside: avoid; text-align: center; }
.pagina-diagrama p { text-align: center; }
.pagina-diagrama img { display: block; margin: 0 auto; max-height: 340mm; max-width: 265mm; object-fit: contain; }
details { display: block; margin: 4px 0; }
summary { font-size: 9pt; font-weight: bold; }
.jp-OutputArea { display: block !important; }
.jp-OutputArea-child { display: block !important; }
'''
        documento.head.append(estilo)
        # As tabelas longas têm amostra identificada; os resultados integrais ficam no notebook.
        caminho_html = saida / 'Saúde da Mulher na África Subsaariana.html'
        caminho_html.write_text(str(documento), encoding='utf-8')
        pagina.goto(caminho_html.as_uri(), wait_until='networkidle')
        pagina.evaluate('document.fonts.ready')
        assert pagina.locator('img').evaluate_all('(imagens) => imagens.every(i => i.complete && i.naturalWidth > 0)'), 'Imagem ausente.'
        pagina.pdf(path=str(saida / 'Saúde da Mulher na África Subsaariana.pdf'),
                   print_background=True, prefer_css_page_size=True,
                   display_header_footer=True, header_template='<span></span>',
                   footer_template='<div style="font:8px Arial;width:100%;text-align:center"><span class="pageNumber"></span> / <span class="totalPages"></span></div>')
        navegador.close()
    print('Diagramas PNG, HTML e PDF exportados.')


if __name__ == '__main__':
    main()
