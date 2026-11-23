"""Renderiza o modelo relacional com Mermaid, sem alterar o ER original."""
from pathlib import Path
import re
from playwright.sync_api import sync_playwright, Error

RAIZ = Path(__file__).resolve().parents[1]


def main():
    biblioteca = RAIZ / 'tmp/diagramas/node_modules/mermaid/dist/mermaid.min.js'
    if not biblioteca.exists():
        raise SystemExit('Instale: npm install --prefix tmp/diagramas --no-audit --no-fund mermaid')
    fonte = (RAIZ / 'docs/Diagrama Relacional.mmd').read_text(encoding='utf-8')
    with sync_playwright() as p:
        try:
            navegador = p.chromium.launch(channel='msedge', headless=True)
        except Error:
            navegador = p.chromium.launch(headless=True)
        pagina = navegador.new_page(device_scale_factor=2)
        pagina.set_content('<html><body></body></html>')
        pagina.add_script_tag(path=str(biblioteca))
        pagina.evaluate("mermaid.initialize({startOnLoad: false, securityLevel: 'strict'})")
        svg = pagina.evaluate('''async fonte => {
            await mermaid.parse(fonte);
            return (await mermaid.render('relacional', fonte)).svg;
        }''', fonte)
        _, _, largura, altura = map(float, re.search(r'viewBox="([^"]+)"', svg).group(1).split())
        svg = re.sub(r'width="100%"', f'width="{largura}px" height="{altura}px"', svg, count=1)
        caminho = RAIZ / 'docs/Diagrama Relacional.svg'
        caminho.write_text(svg, encoding='utf-8')
        pagina.goto(caminho.as_uri())
        pagina.locator('svg').screenshot(path=str(caminho.with_suffix('.png')))
        navegador.close()
    print('Mermaid validado; SVG e PNG gerados. ER original preservado.')


if __name__ == '__main__':
    main()
