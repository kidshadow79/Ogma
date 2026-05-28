import re
import base64
from nicegui import ui

def extract_html_blocks(content: str) -> list:
    """
    Parcourt le contenu pour isoler les blocs de code HTML (```html ... ```) du reste du markdown.
    Gère également de façon robuste les blocs non fermés si la réponse a été tronquée.
    Retourne une liste de dictionnaires de type :
        [{'type': 'markdown', 'content': '...'}, {'type': 'html', 'content': '...'}]
    """
    blocks = []
    pos = 0
    while True:
        start_idx = content.find("```html", pos)
        if start_idx == -1:
            if pos < len(content):
                blocks.append({
                    'type': 'markdown',
                    'content': content[pos:]
                })
            break
        
        if start_idx > pos:
            blocks.append({
                'type': 'markdown',
                'content': content[pos:start_idx]
            })
        
        content_start = start_idx + 7
        end_idx = content.find("```", content_start)
        if end_idx == -1:
            # Bloc HTML non fermé, tout le reste est considéré comme HTML
            html_code = content[content_start:].strip()
            # Nettoyer d'éventuelles balises de formatage cassées
            blocks.append({
                'type': 'html',
                'content': html_code
            })
            break
        else:
            # Bloc HTML fermé
            html_code = content[content_start:end_idx].strip()
            blocks.append({
                'type': 'html',
                'content': html_code
            })
            pos = end_idx + 3
            
    return blocks

def render_html_preview(html_content: str):
    """
    Génère un widget NiceGUI de prévisualisation interactive (carte repliable)
    pour le code HTML fourni, avec support d'affichage, téléchargement et ouverture dans un nouvel onglet.
    """
    # Encodage Base64 pour le transfert et le chargement sécurisé dans l'iframe
    html_bytes = html_content.encode('utf-8')
    html_base64 = base64.b64encode(html_bytes).decode('utf-8')

    with ui.card().classes('w-full').style(
        'background: rgba(30, 30, 45, 0.6); '
        'border: 1px solid rgba(255, 184, 108, 0.35); '
        'box-shadow: 0 4px 16px rgba(0,0,0,0.4); '
        'border-radius: 8px; '
        'padding: 12px; '
        'margin: 8px 0;'
    ):
        with ui.row().classes('w-full items-center justify-between gap-2'):
            with ui.row().classes('items-center gap-2'):
                ui.icon('html', color='orange').style('font-size: 24px;')
                ui.label('Page HTML interactive').style('font-weight: bold; color: var(--accent-gold, #ffb86c); font-size: 15px;')
            
            with ui.row().classes('items-center gap-2'):
                is_visible = False
                
                # Conteneur de l'iframe
                iframe_container = ui.element('div').classes('w-full mt-2')
                iframe_container.style('display: none;')

                def toggle_preview(e):
                    nonlocal is_visible
                    is_visible = not is_visible
                    iframe_container.style(f'display: {"block" if is_visible else "none"}')
                    toggle_btn.set_text('Masquer' if is_visible else 'Visualiser')
                    toggle_btn.props(f'icon={"visibility_off" if is_visible else "visibility"}')

                toggle_btn = ui.button('Visualiser', icon='visibility', on_click=toggle_preview).props('flat dense').style('color: var(--accent-gold, #ffb86c);')

                def open_new_tab():
                    js_code = f"""
                    (function() {{
                        const base64Content = "{html_base64}";
                        const binaryString = atob(base64Content);
                        const bytes = new Uint8Array(binaryString.length);
                        for (let i = 0; i < binaryString.length; i++) {{
                            bytes[i] = binaryString.charCodeAt(i);
                        }}
                        const blob = new Blob([bytes], {{type: 'text/html;charset=utf-8'}});
                        const url = URL.createObjectURL(blob);
                        window.open(url, '_blank');
                    }})();
                    """
                    ui.run_javascript(js_code)

                open_btn = ui.button('Ouvrir', icon='open_in_new', on_click=open_new_tab).props('flat dense').style('color: #8be9fd;')

                def download_file():
                    js_code = f"""
                    (function() {{
                        const base64Content = "{html_base64}";
                        const binaryString = atob(base64Content);
                        const bytes = new Uint8Array(binaryString.length);
                        for (let i = 0; i < binaryString.length; i++) {{
                            bytes[i] = binaryString.charCodeAt(i);
                        }}
                        const blob = new Blob([bytes], {{type: 'text/html;charset=utf-8'}});
                        const url = URL.createObjectURL(blob);
                        const a = document.createElement('a');
                        a.href = url;
                        a.download = 'ogma_artifact.html';
                        document.body.appendChild(a);
                        a.click();
                        document.body.removeChild(a);
                        URL.revokeObjectURL(url);
                    }})();
                    """
                    ui.run_javascript(js_code)

                download_btn = ui.button('Télécharger', icon='download', on_click=download_file).props('flat dense').style('color: #50fa7b;')

        # Iframe injecté dans son conteneur
        with iframe_container:
            ui.html(
                f'<iframe src="data:text/html;base64,{html_base64}" '
                f'style="width: 100%; height: 500px; border: 1px solid rgba(255,255,255,0.15); '
                f'background: white; border-radius: 4px;"></iframe>'
            )
