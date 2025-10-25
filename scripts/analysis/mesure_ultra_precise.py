#!/usr/bin/env python3
"""
MESURE ULTRA PRÉCISE - Identifier l'écart exact
"""

from nicegui import ui, app
from pathlib import Path

@ui.page('/')
def mesure_page():
    ui.dark_mode()
    
    app.add_static_files('/static', Path(__file__).parent / 'static')
    ui.add_head_html('<link rel="stylesheet" href="/static/ogma_styles.css" />')
    
    # CSS avec mesures ultra précises
    ui.add_head_html('''
    <style>
    /* Bordures pour voir les éléments */
    .conversation-area { border: 3px solid blue !important; }
    .chat-centering-layer { border: 3px solid cyan !important; }
    
    /* Règles de référence */
    .ruler-center {
        position: fixed;
        top: 0;
        bottom: 0;
        left: calc(368px + (100vw - 368px) / 2);
        width: 3px;
        background: yellow;
        z-index: 9999;
        opacity: 1;
    }
    
    /* Diagnostic ultra précis */
    .diagnostic-ultra {
        position: fixed;
        top: 10px;
        left: 10px;
        background: rgba(0,0,0,0.95);
        color: white;
        padding: 20px;
        border-radius: 8px;
        font-family: monospace;
        z-index: 9999;
        font-size: 12px;
        line-height: 1.4;
        max-width: 350px;
    }
    </style>
    ''')
    
    # Script de mesure ultra précise
    ui.add_body_html('''
    <div class="ruler-center"></div>
    
    <div class="diagnostic-ultra">
        <div style="color: yellow; font-weight: bold; margin-bottom: 15px;">🔍 MESURE ULTRA PRÉCISE</div>
        
        <div><strong>Dimensions écran :</strong></div>
        <div>Largeur : <span id="screen-w">?</span>px</div>
        <div>Sidebar : 368px (fixe)</div>
        <div>Espace dispo : <span id="available-w">?</span>px</div>
        
        <div style="margin: 15px 0;"><strong>Positions théoriques :</strong></div>
        <div>Centre théorique : <span id="center-theo">?</span>px</div>
        <div>Règle jaune : <span id="ruler-pos">?</span>px</div>
        
        <div style="margin: 15px 0;"><strong>Positions réelles :</strong></div>
        <div>Cadre bleu - gauche : <span id="blue-left">?</span>px</div>
        <div>Cadre bleu - droite : <span id="blue-right">?</span>px</div>
        <div>Cadre bleu - centre : <span id="blue-center">?</span>px</div>
        
        <div style="margin: 15px 0;"><strong>DIAGNOSTIC :</strong></div>
        <div style="color: lime; font-weight: bold;">Écart centre : <span id="ecart">?</span>px</div>
        <div style="color: orange;">Direction : <span id="direction">?</span></div>
    </div>
    
    <script>
    function mesureUltraPrecise() {
        try {
            const screenW = window.innerWidth;
            const availableSpace = screenW - 368;
            const centerTheo = 368 + (availableSpace / 2);
            const rulerPos = centerTheo;
            
            document.getElementById('screen-w').textContent = screenW;
            document.getElementById('available-w').textContent = availableSpace;
            document.getElementById('center-theo').textContent = Math.round(centerTheo);
            document.getElementById('ruler-pos').textContent = Math.round(rulerPos);
            
            // Mesurer le cadre bleu
            const blueFrame = document.querySelector('.conversation-area');
            if (blueFrame) {
                const rect = blueFrame.getBoundingClientRect();
                const blueLeft = Math.round(rect.left);
                const blueRight = Math.round(rect.right);
                const blueCenter = Math.round(blueLeft + rect.width / 2);
                const ecart = Math.round(blueCenter - centerTheo);
                
                document.getElementById('blue-left').textContent = blueLeft;
                document.getElementById('blue-right').textContent = blueRight;
                document.getElementById('blue-center').textContent = blueCenter;
                document.getElementById('ecart').textContent = ecart;
                
                if (ecart < 0) {
                    document.getElementById('direction').textContent = 'TROP À GAUCHE';
                    document.getElementById('direction').style.color = 'red';
                } else if (ecart > 0) {
                    document.getElementById('direction').textContent = 'TROP À DROITE';
                    document.getElementById('direction').style.color = 'orange';
                } else {
                    document.getElementById('direction').textContent = 'PARFAIT';
                    document.getElementById('direction').style.color = 'lime';
                }
                
                // Colorer l'écart
                const ecartEl = document.getElementById('ecart');
                if (Math.abs(ecart) <= 2) {
                    ecartEl.style.color = 'lime';
                } else if (Math.abs(ecart) <= 10) {
                    ecartEl.style.color = 'orange';
                } else {
                    ecartEl.style.color = 'red';
                }
            }
        } catch (error) {
            console.error('Erreur mesure ultra précise:', error);
        }
    }
    
    setInterval(mesureUltraPrecise, 500);
    setTimeout(mesureUltraPrecise, 1000);
    </script>
    ''')
    
    # Structure simple pour focus sur la mesure
    with ui.element('div').classes('app-header'):
        ui.label('MESURE ULTRA PRÉCISE').classes('app-subtitle')
    
    with ui.element('div').classes('app-body'):
        with ui.element('div').classes('sidebar'):
            ui.label('SIDEBAR 368px').style('color: white; text-align: center; padding: 20px;')
            
        with ui.element('main').classes('chat-panel'):
            with ui.element('div').props('data-role="chat-viewport"') as viewport:
                viewport.style('display:flex; flex-direction:column; height:100%; width:100%;')
                with ui.element('div').classes('conversation-area').props('data-role="chat-scroll"'):
                    with ui.element('div').classes('chat-viewport-layer').props('data-role="viewport-layer"'):
                        with ui.element('div').classes('chat-centering-layer').props('data-role="centering-layer"'):
                            with ui.element('div').classes('chat-inner').props('data-role="chat-container"'):
                                ui.label('🎯 FOCUS : CADRE BLEU vs RÈGLE JAUNE').style('text-align: center; color: yellow; margin: 50px 0; font-size: 16px; font-weight: bold;')
                                ui.label('Regarde le diagnostic en haut à gauche !').style('text-align: center; color: white; margin: 20px 0;')

if __name__ == '__main__':
    ui.run(
        title="Mesure Ultra Précise",
        host="localhost", 
        port=8093,
        show=True,
        reload=False
    )