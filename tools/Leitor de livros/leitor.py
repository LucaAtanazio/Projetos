import sys
import os
import json
import pytesseract
from PIL import Image
from PIL.ImageQt import ImageQt
from PyQt6.QtWidgets import (QApplication, QMainWindow, QLabel, QVBoxLayout, 
                             QHBoxLayout, QWidget, QPushButton, QFileDialog, 
                             QLineEdit, QListWidget, QSplitter, QStackedWidget,
                             QListView, QListWidgetItem, QSlider, QMenu, QMessageBox,
                             QCheckBox, QGraphicsOpacityEffect)
from PyQt6.QtGui import QPixmap, QIcon, QAction, QKeyEvent
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QSize, QPropertyAnimation, QEasingCurve

ARQUIVO_BIBLIOTECA = "biblioteca.json"
# Lista expandida de extensões suportadas
EXTENSOES_SUPORTADAS = ('.png', '.jpg', '.jpeg', '.webp', '.jp2', '.bmp', '.tiff')

STYLE_GLOBAL = """
QMainWindow { background-color: #0b0b1a; }
QPushButton {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #8c9eff, stop:1 #3d5afe);
    border: 1px solid #a8b1ff; border-radius: 8px; color: white; font-weight: bold; padding: 8px;
}
QPushButton:hover { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #a8b1ff, stop:1 #536dfe); }
QLineEdit, QListWidget {
    background-color: #1a1a2e; color: #e0e0e0; border: 1px solid #3d5afe; border-radius: 5px;
}
QToolTip {
    background-color: rgba(26, 26, 46, 220);
    color: #8c9eff; border: 1px solid #3d5afe; font-weight: bold; padding: 5px;
}
"""

class OcrThread(QThread):
    resultado_pronto = pyqtSignal(int, str)
    progresso = pyqtSignal(int)

    def __init__(self, caminhos_imagens, pasta_cache):
        super().__init__()
        self.caminhos = caminhos_imagens
        self.pasta_cache = pasta_cache
        self.cache_file = os.path.join(pasta_cache, "ocr_cache.json")
        self.rodando = True

    def run(self):
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, "r", encoding="utf-8") as f:
                    dados_cache = json.load(f)
                    for i, txt in dados_cache.items():
                        self.resultado_pronto.emit(int(i), txt)
                return
            except: pass

        cache_acumulado = {}
        for index, caminho in enumerate(self.caminhos):
            if not self.rodando: break
            try:
                texto = pytesseract.image_to_string(Image.open(caminho), lang='por').lower()
                self.resultado_pronto.emit(index, texto)
                cache_acumulado[index] = texto
                self.progresso.emit(index + 1)
            except: pass
        
        try:
            with open(self.cache_file, "w", encoding="utf-8") as f:
                json.dump(cache_acumulado, f, ensure_ascii=False)
        except: pass
        pass

    def parar(self):
        self.rodando = False
        self.wait()

class LeitorUniversal(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("L.I.V.E. - Engine de Leitura")
        self.setGeometry(100, 100, 1280, 800)
        self.setStyleSheet(STYLE_GLOBAL)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        self.biblioteca = {}
        self.carregar_dados()

        self.paginas = []
        self.indice_atual = 0
        self.banco_texto = {}
        self.thread_ocr = None
        self.livro_atual = None

        self.setup_ui()
        self.atualizar_galeria()

    def carregar_dados(self):
        if os.path.exists(ARQUIVO_BIBLIOTECA):
            try:
                with open(ARQUIVO_BIBLIOTECA, "r", encoding="utf-8") as f:
                    self.biblioteca = json.load(f)
            except: self.biblioteca = {}

    def salvar_dados(self):
        with open(ARQUIVO_BIBLIOTECA, "w", encoding="utf-8") as f:
            json.dump(self.biblioteca, f, ensure_ascii=False, indent=4)

    def setup_ui(self):
        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        # GALERIA
        tela_galeria = QWidget()
        layout_galeria = QVBoxLayout(tela_galeria)
        self.lista_galeria = QListWidget()
        self.lista_galeria.setViewMode(QListView.ViewMode.IconMode)
        self.lista_galeria.setIconSize(QSize(180, 260))
        self.lista_galeria.setSpacing(30)
        self.lista_galeria.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.lista_galeria.customContextMenuRequested.connect(self.mostrar_menu_contexto_galeria)
        self.lista_galeria.itemDoubleClicked.connect(self.abrir_livro)
        
        btn_add = QPushButton("➕ Adicionar HQ/Pasta")
        btn_add.clicked.connect(self.adicionar_livro_galeria)
        layout_galeria.addWidget(btn_add)
        layout_galeria.addWidget(self.lista_galeria)
        self.stack.addWidget(tela_galeria)

        # LEITOR
        self.tela_leitor = QWidget()
        layout_principal = QHBoxLayout(self.tela_leitor)
        
        self.painel_lateral = QVBoxLayout()
        self.btn_voltar = QPushButton("⬅ Galeria")
        self.btn_voltar.clicked.connect(self.voltar_para_galeria)
        self.barra_busca = QLineEdit()
        self.barra_busca.setPlaceholderText("Buscar termo...")
        self.barra_busca.returnPressed.connect(self.realizar_busca_ocr)
        self.lista_resultados = QListWidget()
        self.lista_resultados.itemClicked.connect(self.ir_para_resultado)
        self.chk_dupla = QCheckBox("Modo Duplo")
        self.chk_dupla.stateChanged.connect(self.mostrar_pagina)
        self.lbl_status_ocr = QLabel("OCR: Próximo")
        self.lbl_status_ocr.setStyleSheet("color: #5c6bc0; font-size: 10px;")

        self.painel_lateral.addWidget(self.btn_voltar)
        self.painel_lateral.addWidget(self.barra_busca)
        self.painel_lateral.addWidget(self.lista_resultados)
        self.painel_lateral.addWidget(self.chk_dupla)
        self.painel_lateral.addWidget(self.lbl_status_ocr)

        self.area_leitura = QWidget()
        layout_img = QHBoxLayout(self.area_leitura)
        self.lbl_esq = QLabel(); self.lbl_esq.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_dir = QLabel(); self.lbl_dir.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.eff_esq = QGraphicsOpacityEffect(self.lbl_esq); self.lbl_esq.setGraphicsEffect(self.eff_esq)
        self.eff_dir = QGraphicsOpacityEffect(self.lbl_dir); self.lbl_dir.setGraphicsEffect(self.eff_dir)
        
        layout_img.addWidget(self.lbl_esq)
        layout_img.addWidget(self.lbl_dir)

        self.area_leitura.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.area_leitura.customContextMenuRequested.connect(self.mostrar_menu_contexto_leitura)

        layout_leitor_v = QVBoxLayout()
        layout_leitor_v.addWidget(self.area_leitura, stretch=1)
        
        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.valueChanged.connect(self.mudar_pagina_pelo_slider)
        layout_leitor_v.addWidget(self.slider)

        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        w_lat = QWidget(); w_lat.setLayout(self.painel_lateral)
        w_lei = QWidget(); w_lei.setLayout(layout_leitor_v)
        self.splitter.addWidget(w_lat); self.splitter.addWidget(w_lei)
        self.splitter.setSizes([200, 1000])
        
        layout_principal.addWidget(self.splitter)
        self.stack.addWidget(self.tela_leitor)

    def animar_passagem(self):
        self.anims = []
        for eff in [self.eff_esq, self.eff_dir]:
            anim = QPropertyAnimation(eff, b"opacity")
            anim.setDuration(250)
            anim.setStartValue(0.3)
            anim.setEndValue(1.0)
            anim.setEasingCurve(QEasingCurve.Type.OutQuad)
            anim.start()
            self.anims.append(anim)

    def proxima_pagina(self):
        salto = 2 if self.chk_dupla.isChecked() and self.indice_atual > 0 else 1
        if self.indice_atual + salto < len(self.paginas):
            self.indice_atual += salto
            self.animar_passagem()
            self.mostrar_pagina()

    def pagina_anterior(self):
        salto = 2 if self.chk_dupla.isChecked() and self.indice_atual > 2 else 1
        self.indice_atual = max(0, self.indice_atual - salto)
        self.animar_passagem()
        self.mostrar_pagina()

    def keyPressEvent(self, event: QKeyEvent):
        if self.stack.currentIndex() == 1:
            sentido = self.biblioteca[self.livro_atual].get("sentido", "ocidental")
            if event.key() == Qt.Key.Key_Right:
                self.proxima_pagina() if sentido == "ocidental" else self.pagina_anterior()
            elif event.key() == Qt.Key.Key_Left:
                self.pagina_anterior() if sentido == "ocidental" else self.proxima_pagina()
        super().keyPressEvent(event)

    def mostrar_menu_contexto_leitura(self, pos):
        menu = QMenu()
        acao_marcar = menu.addAction("📌 Marcar esta página")
        acao = menu.exec(self.area_leitura.mapToGlobal(pos))
        if acao == acao_marcar:
            self.biblioteca[self.livro_atual]["marcador"] = self.indice_atual
            self.salvar_dados()
            QMessageBox.information(self, "L.I.V.E.", f"Página {self.indice_atual + 1} marcada!")

    def atualizar_galeria(self):
        self.lista_galeria.clear()
        for titulo, dados in self.biblioteca.items():
            pasta = dados.get("caminho")
            if not pasta or not os.path.exists(pasta): continue
            
            try:
                arqs = sorted([f for f in os.listdir(pasta) if f.lower().endswith(EXTENSOES_SUPORTADAS)])
                if arqs:
                    # Carregamento seguro da capa
                    try:
                        img_capa = Image.open(os.path.join(pasta, arqs[0])).convert("RGBA")
                        pix = QPixmap.fromImage(ImageQt(img_capa))
                        icon = QIcon(pix)
                    except:
                        icon = QIcon() # Ícone vazio se falhar

                    item = QListWidgetItem(icon, titulo)
                    marcador = dados.get("marcador", 0)
                    item.setToolTip(f"Página marcada: {marcador + 1}/{len(arqs)}")
                    item.setData(Qt.ItemDataRole.UserRole, titulo)
                    self.lista_galeria.addItem(item)
            except Exception as e:
                print(f"Erro ao processar {titulo}: {e}")

    def mostrar_menu_contexto_galeria(self, pos):
        item = self.lista_galeria.itemAt(pos)
        if not item: return
        livro = item.text()
        menu = QMenu()
        ori = menu.addAction("Sentido Oriental" + (" ✓" if self.biblioteca[livro].get("sentido")=="oriental" else ""))
        oci = menu.addAction("Sentido Ocidental" + (" ✓" if self.biblioteca[livro].get("sentido")=="ocidental" else ""))
        menu.addSeparator()
        del_b = menu.addAction("Esquecer Livro")
        
        acao = menu.exec(self.lista_galeria.mapToGlobal(pos))
        if acao == ori: self.biblioteca[livro]["sentido"] = "oriental"
        elif acao == oci: self.biblioteca[livro]["sentido"] = "ocidental"
        elif acao == del_b:
            del self.biblioteca[livro]
            self.salvar_dados()
            self.atualizar_galeria()
        self.salvar_dados()

    def abrir_livro(self, item):
        self.livro_atual = item.data(Qt.ItemDataRole.UserRole)
        dados = self.biblioteca[self.livro_atual]
        self.indice_atual = dados.get("marcador", 0)
        
        self.tela_leitor.setLayoutDirection(Qt.LayoutDirection.RightToLeft if dados.get("sentido")=="oriental" else Qt.LayoutDirection.LeftToRight)
        
        pasta = dados["caminho"]
        self.paginas = sorted([os.path.join(pasta, f) for f in os.listdir(pasta) if f.lower().endswith(EXTENSOES_SUPORTADAS)])
        
        if self.paginas:
            self.slider.setMaximum(len(self.paginas)-1)
            self.mostrar_pagina()
            self.iniciar_ocr(pasta)
            self.stack.setCurrentIndex(1)
            self.setFocus()

    def voltar_para_galeria(self):
            if self.thread_ocr and self.thread_ocr.isRunning():
                self.thread_ocr.parar()
            self.atualizar_galeria()
            self.stack.setCurrentIndex(0)

    def mostrar_pagina(self):
        if not self.paginas: return
        sentido = self.biblioteca[self.livro_atual].get("sentido", "ocidental")
        duplo = self.chk_dupla.isChecked()
        
        self.lbl_esq.clear(); self.lbl_dir.clear()
        
        if not duplo:
            self.lbl_esq.hide()
            self.renderizar(self.lbl_dir, self.indice_atual)
        else:
            self.lbl_esq.show()
            if self.indice_atual == 0:
                t = self.lbl_dir if sentido == "ocidental" else self.lbl_esq
                self.renderizar(t, 0)
            else:
                idx = self.indice_atual if self.indice_atual % 2 != 0 else self.indice_atual - 1
                ie, idir = (idx, idx+1) if sentido == "ocidental" else (idx+1, idx)
                self.renderizar(self.lbl_esq, ie)
                self.renderizar(self.lbl_dir, idir)

        self.slider.blockSignals(True); self.slider.setValue(self.indice_atual); self.slider.blockSignals(False)

    def renderizar(self, label, idx):
        if 0 <= idx < len(self.paginas):
            try:
                img = Image.open(self.paginas[idx]).convert("RGBA")
                pix = QPixmap.fromImage(ImageQt(img))
                label.setPixmap(pix.scaled(label.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
            except: label.setText("Erro ao carregar imagem")

    def iniciar_ocr(self, pasta):
        self.banco_texto = {}
        self.lbl_status_ocr.setText("OCR: Lendo Cache...")
        self.thread_ocr = OcrThread(self.paginas, pasta)
        self.thread_ocr.resultado_pronto.connect(lambda i, t: self.banco_texto.update({i: t}))
        self.thread_ocr.progresso.connect(lambda p: self.lbl_status_ocr.setText(f"OCR: {p}/{len(self.paginas)}"))
        self.thread_ocr.start()

    def realizar_busca_ocr(self):
        termo = self.barra_busca.text().lower().strip()
        self.lista_resultados.clear()
        if not termo: return
        for idx, txt in self.banco_texto.items():
            if termo in txt: self.lista_resultados.addItem(f"Página {idx + 1}")

    def ir_para_resultado(self, item):
        self.indice_atual = int(item.text().replace("Página ", "")) - 1
        self.animar_passagem()
        self.mostrar_pagina()

    def mudar_pagina_pelo_slider(self, v):
        self.indice_atual = v
        self.mostrar_pagina()

    def adicionar_livro_galeria(self):
        p = QFileDialog.getExistingDirectory(self, "Selecionar HQ")
        if p:
            self.biblioteca[os.path.basename(p)] = {"caminho": p, "sentido": "ocidental", "marcador": 0}
            self.salvar_dados()
            self.atualizar_galeria()

    def resizeEvent(self, e):
        if self.stack.currentIndex() == 1: self.mostrar_pagina()
        super().resizeEvent(e)

    def closeEvent(self, event):
        if self.thread_ocr and self.thread_ocr.isRunning():
            self.thread_ocr.parar()
        event.accept()        

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = LeitorUniversal()
    win.show()
    sys.exit(app.exec())