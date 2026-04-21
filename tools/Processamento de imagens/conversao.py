import os
import rawpy
import fitz
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageTk
from pillow_heif import register_heif_opener
from svglib.svglib import svg2rlg
from reportlab.graphics import renderPM

register_heif_opener()

class ConversorBatchPro:
    def __init__(self, root):
        self.root = root
        self.root.title("Studio Pro - Batch Edition")

        self.root.configure(bg="#121212")
        

        self.caminhos_alvo = []
        self.arquivo_atual = None
        self.arquivo_resultado = None
        self.formato_destino = tk.StringVar(value="JPG")
        self.manter_original = tk.BooleanVar(value=False)
        
        self.setup_ui()
        
        self.lista_batch.bind('<<ListboxSelect>>', self.ao_selecionar_item)


    def setup_ui(self):
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("TFrame", background="#121212")
        style.configure("TLabel", background="#121212", foreground="#e0e0e0")
        style.configure("TCheckbutton", background="#121212", foreground="#e0e0e0")

        self.root.geometry("1100x850")
        self.root.resizable(False, False)

        self.main_frame = ttk.Frame(self.root, padding="30")
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        header_frame = ttk.Frame(self.main_frame)
        header_frame.pack(fill=tk.X, pady=(0, 20))

        self.btn_file = tk.Button(header_frame, text="SELECIONAR ARQUIVO(S)", command=self.selecionar_arquivos,
                                 bg="#3d5afe", fg="white", font=("Arial", 10, "bold"), padx=15, pady=8, relief="flat")
        self.btn_file.pack(side=tk.LEFT, padx=5)

        self.btn_dir = tk.Button(header_frame, text="SELECIONAR PASTA", command=self.selecionar_pasta,
                                bg="#673ab7", fg="white", font=("Arial", 10, "bold"), padx=15, pady=8, relief="flat")
        self.btn_dir.pack(side=tk.LEFT, padx=5)

        self.lbl_status_topo = ttk.Label(header_frame, text="Nenhum item selecionado", font=("Arial", 10, "italic"))
        self.lbl_status_topo.pack(side=tk.RIGHT, padx=10)

        self.display_frame = ttk.Frame(self.main_frame)
        self.display_frame.pack(fill=tk.BOTH, expand=True)

        self.preview_container = ttk.Frame(self.display_frame, height=400)
        self.preview_container.pack(fill=tk.X, pady=10)
        self.preview_container.pack_propagate(False)
        
        self.lbl_img_origem = ttk.Label(self.preview_container, cursor="hand2")
        self.lbl_img_origem.pack(side=tk.LEFT, expand=True)
        self.lbl_img_origem.bind("<Button-1>", lambda e: self.abrir_zoom())
        
        ttk.Label(self.preview_container, text="➠", font=("Arial", 30), foreground="#3d5afe").pack(side=tk.LEFT, padx=15)
        

        self.lbl_img_destino = ttk.Label(self.preview_container, cursor="hand2") # Adicionei o cursor hand2
        self.lbl_img_destino.pack(side=tk.LEFT, expand=True)
        self.lbl_img_destino.bind("<Button-1>", lambda e: self.abrir_zoom(lado="destino")) # Bind novo

        self.lista_batch = tk.Listbox(self.display_frame, bg="#1e1e1e", fg="#00c853", border=0, font=("Consolas", 10), height=10)
        self.lista_batch.pack(fill=tk.BOTH, expand=True, pady=10)

        bottom_bar = ttk.Frame(self.main_frame)
        bottom_bar.pack(fill=tk.X, side=tk.BOTTOM, pady=20)

        self.check_manter = ttk.Checkbutton(bottom_bar, text="Manter originais?", variable=self.manter_original)
        self.check_manter.pack(side=tk.LEFT, padx=20)

        ttk.Label(bottom_bar, text="Formato:").pack(side=tk.LEFT, padx=5)
        self.combo = ttk.Combobox(bottom_bar, values=["JPG", "PNG", "WEBP", "PDF", "ICO"], textvariable=self.formato_destino, width=8, state="readonly")
        self.combo.pack(side=tk.LEFT, padx=5)

        self.btn_executar = tk.Button(bottom_bar, text="INICIAR PROCESSAMENTO", command=self.executar,
                                     bg="#00c853", fg="white", font=("Arial", 11, "bold"), padx=30, relief="flat")
        self.btn_executar.pack(side=tk.RIGHT, padx=20)
        pass

    def abrir_zoom(self, lado="origem"):
        caminho = self.arquivo_atual if lado == "origem" else self.arquivo_resultado
        
        if not caminho or not os.path.exists(caminho):
            return

        zoom_win = tk.Toplevel(self.root)
        zoom_win.attributes("-fullscreen", True)
        zoom_win.configure(bg="black")

        try:
            if caminho.lower().endswith(('.raw', '.dng')):
                with rawpy.imread(caminho) as raw:
                    img_full = Image.fromarray(raw.postprocess(use_camera_wb=True, half_size=True))
            else:
                img_full = Image.open(caminho)

            screen_w = zoom_win.winfo_screenwidth()
            screen_h = zoom_win.winfo_screenheight()
            img_full.thumbnail((screen_w, screen_h))
            
            tk_full = ImageTk.PhotoImage(img_full)
            lbl_full = tk.Label(zoom_win, image=tk_full, bg="black")
            lbl_full.image = tk_full
            lbl_full.pack(expand=True)
            
            zoom_win.bind("<Escape>", lambda e: zoom_win.destroy())
        except Exception as e:
            if zoom_win.winfo_exists():
                zoom_win.destroy()
            print(f"Erro no Zoom: {e}")

    def ao_selecionar_item(self, event):
            selecao = self.lista_batch.curselection()
            if not selecao:
                return
            
            indice = selecao[0]
            caminho_clicado = self.caminhos_alvo[indice]
            
            img_preview = self.gerar_preview(caminho_clicado)
            if img_preview:
                self.lbl_img_origem.config(image=img_preview, text="")
                self.lbl_img_origem.image = img_preview
                self.lbl_img_destino.config(image='', text="[Aguardando Processamento]")
            else:
                self.lbl_img_origem.config(image='', text="[Visualização não disponível]")


    def selecionar_arquivos(self):
        paths = filedialog.askopenfilenames()
        if paths:
            self.caminhos_alvo = list(paths)
            self.atualizar_ui_selecao()

    def selecionar_pasta(self):
        folder = filedialog.askdirectory()
        if folder:
            exts = ('.heic', '.png', '.webp', '.bmp', '.gif', '.ico', '.raw', '.dng', '.svg', '.jpg', '.jpeg')
            self.caminhos_alvo = [os.path.join(folder, f) for f in os.listdir(folder) if f.lower().endswith(exts)]
            self.atualizar_ui_selecao()

    def atualizar_ui_selecao(self):
        count = len(self.caminhos_alvo)
        self.lbl_status_topo.config(text=f"{count} item(s) selecionado(s)")
        self.lista_batch.delete(0, tk.END)
        
        for path in self.caminhos_alvo:
            self.lista_batch.insert(tk.END, f" 📁 {os.path.basename(path)}")
        
        if count > 0:
            img = self.gerar_preview(self.caminhos_alvo[0])
            self.lbl_img_origem.config(image=img, text="")
            self.lbl_img_origem.image = img

    def gerar_preview(self, caminho):
        try:
            if not os.path.exists(caminho): return None
            self.arquivo_atual = caminho 
            ext = os.path.splitext(caminho)[1].lower()

            if ext == '.pdf':
                doc = fitz.open(caminho)
                pagina = doc.load_page(0)
                pix = pagina.get_pixmap()
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                doc.close()
            elif ext in ['.raw', '.dng']:
                with rawpy.imread(caminho) as raw:
                    img = Image.fromarray(raw.postprocess(use_camera_wb=True, half_size=True))
            else:
                img = Image.open(caminho)

            img.thumbnail((380, 380)) 
            return ImageTk.PhotoImage(img)
        except Exception as e:
            print(f"Erro na preview: {e}")
            return None

    def converter_unitario(self, origem, fmt_dest):
        nome_base = os.path.splitext(origem)[0]
        saida = f"{nome_base}.{fmt_dest.lower()}"
        fmt_pillow = "JPEG" if fmt_dest == "JPG" else fmt_dest
        
        if origem.lower().endswith('.pdf'):
            doc = fitz.open(origem)
            pagina = doc.load_page(0)
            pix = pagina.get_pixmap()
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            doc.close()
        elif origem.lower().endswith('.svg'):
            drawing = svg2rlg(origem)
            renderPM.drawToFile(drawing, saida, fmt=fmt_pillow)
            return saida
        elif origem.lower().endswith(('.raw', '.dng')):
            with rawpy.imread(origem) as raw:
                img = Image.fromarray(raw.postprocess())
        else:
            img = Image.open(origem)
        
        if fmt_dest in ["PDF", "JPG"]: img = img.convert("RGB")
        img.save(saida, fmt_pillow, quality=95)
        
        if not self.manter_original.get():
            os.remove(origem)
        return saida

    def executar(self):
        if not self.caminhos_alvo: return
        
        fmt = self.formato_destino.get()
        ultimo_gerado = None
        sucessos = 0

        selecao_atual = self.lista_batch.curselection()
        caminho_foco = self.caminhos_alvo[selecao_atual[0]] if selecao_atual else self.caminhos_alvo[-1]
        resultado_foco = None
        
        for path in self.caminhos_alvo:
            try:
                gerado = self.converter_unitario(path, fmt)
                if path == caminho_foco:
                    resultado_foco = gerado
                sucessos += 1
            except Exception as e:
                print(f"Erro: {e}")

        if resultado_foco and os.path.exists(resultado_foco):
            self.arquivo_resultado = resultado_foco
            img_res = self.gerar_preview(resultado_foco)
            if img_res:
                self.lbl_img_destino.config(image=img_res, text="")
                self.lbl_img_destino.image = img_res

        messagebox.showinfo("L.I.V.E. Studio", f"Concluído!\n{sucessos} arquivos processados.")
        
        if not self.manter_original.get():
            self.caminhos_alvo = []
            self.lista_batch.delete(0, tk.END)
            self.lbl_img_origem.config(image='', text="[Original Removido]")

if __name__ == "__main__":
    root = tk.Tk()
    app = ConversorBatchPro(root)
    root.mainloop()