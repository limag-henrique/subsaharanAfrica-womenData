from pathlib import Path
from playwright.sync_api import sync_playwright
root=Path.cwd()
with sync_playwright() as p:
 browser=p.chromium.launch(executable_path='C:/Program Files/Google/Chrome/Application/chrome.exe',headless=True,args=['--allow-file-access-from-files'])
 page=browser.new_page()
 page.goto((root/'tmp/pdfs/notebook.html').as_uri(),wait_until='networkidle')
 page.evaluate('document.fonts.ready')
 page.evaluate("document.querySelectorAll('details').forEach(e=>e.open=true)")
 page.add_style_tag(content='details, .output, .dataframe { max-height:none !important; overflow:visible !important; }')
 page.emulate_media(media='print')
 page.pdf(path=str(root/'output/pdf/Saude_da_Mulher_na_Africa_Subsaariana.pdf'),print_background=True,prefer_css_page_size=True,display_header_footer=True,header_template='<span></span>',footer_template='<div style="font-size:8px;width:100%;text-align:center;color:#666"><span class="pageNumber"></span> / <span class="totalPages"></span></div>')
 browser.close()
print('PDF gerado.')
