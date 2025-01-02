import tkinter as tk
from tkinter import ttk, filedialog
from PIL import Image, ImageTk
import threading
import os
import logging
import time
from image_processor import ImageProcessor, GuiLoggingHandler
import ctypes
import sys
import conversion
import compress as compress_module  
from tkinter import messagebox  

class CustomLogFrame(ttk.Frame):
    def __init__(self, master=None, **kwargs):
        super().__init__(master, **kwargs)
        
        # Criar um widget de texto para exibir os logs
        self.log_text = tk.Text(self, height=5, state='disabled', wrap='word')
        self.log_text.pack(fill='both', expand=True)
        
        # Adicionar uma barra de rolagem
        scrollbar = ttk.Scrollbar(self, command=self.log_text.yview)
        scrollbar.pack(side='right', fill='y')
        self.log_text.configure(yscrollcommand=scrollbar.set)
        
        # Configurar tags de cores para diferentes níveis de log
        self.log_text.tag_configure('INFO', foreground='black')
        self.log_text.tag_configure('WARNING', foreground='orange')
        self.log_text.tag_configure('ERROR', foreground='red')
        self.log_text.tag_configure('SUCCESS', foreground='green')

    def update_log(self, message, level='INFO'):
        # Ativar edição temporariamente
        self.log_text.configure(state='normal')
        
        # Inserir a mensagem com a tag de cor apropriada
        self.log_text.insert(tk.END, message + '\n', level)
        
        # Rolar para o final
        self.log_text.see(tk.END)
        
        # Desativar edição novamente
        self.log_text.configure(state='disabled')

class ImageProcessorGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("NextSmart")
        self.root.geometry("550x500")
        
        self.set_icon()    

        self.progress_var = tk.DoubleVar()
        self.status_var = tk.StringVar()
        self.is_processing = False
        self.processing_started = False
        self.processing_thread = None
        self.images_failed = []
        self.images_successful = []
        self.images_total = 0
        

        # Criar o notebook principal no topo da janela
        self.main_notebook = ttk.Notebook(self.root)
        self.main_notebook.pack(fill='both', expand=True, padx=5, pady=5)

        # Criar os frames para cada aba
        self.basic_frame = ttk.Frame(self.main_notebook)
        self.converter_frame = ttk.Frame(self.main_notebook)
        self.comprimir_frame = ttk.Frame(self.main_notebook)

        # Adicionar as abas ao notebook
        self.main_notebook.add(self.basic_frame, text='Fatiar')
        self.main_notebook.add(self.converter_frame, text='Converter')
        self.main_notebook.add(self.comprimir_frame, text='Comprimir')

        # Configurar a GUI principal no frame Fatiar
        self.setup_gui()

        # Configuração do logger
        self.logger = logging.getLogger("image_processor_gui")
        self.logger.setLevel(logging.DEBUG)

        gui_log_handler = GuiLoggingHandler(update_func=self.update_log)
        gui_log_formatter = logging.Formatter('%(message)s')
        gui_log_handler.setFormatter(gui_log_formatter)

        self.logger.addHandler(gui_log_handler)
        self.logger.propagate = False
        self.logger.info("Aplicação iniciada")
        
        
    def set_icon(self):
        try:
            # Diretório do script
            script_dir = os.path.dirname(os.path.abspath(__file__))
        
            # Caminho do ícone
            icon_path = os.path.join(script_dir, "Logo.ico")

            if os.path.exists(icon_path):
                # Apenas Windows suporta `.ico` diretamente
                if sys.platform.startswith('win'):
                    self.root.iconbitmap(icon_path)
                    print(f"Ícone definido: {icon_path}")
                else:
                    # Outros sistemas usam `.png`
                    img = tk.PhotoImage(file=icon_path)
                    self.root.tk.call('wm', 'iconphoto', self.root._w, img)
                    print(f"Ícone definido: {icon_path}")
            else:
                print("Ícone não encontrado no diretório do script.")

        except Exception as e:
            print(f"Erro ao definir ícone: {e}")

        

    def setup_gui(self):
        # Modificar o parent de todos os widgets para basic_frame ao invés de root
        ttk.Label(self.basic_frame, text="Diretório de Entrada:").pack(pady=5)
        input_frame = ttk.Frame(self.basic_frame)
        input_frame.pack(fill='x', padx=20)

        self.input_entry = ttk.Entry(input_frame)
        self.input_entry.pack(side='left', fill='x', expand=True)
        ttk.Button(input_frame, text="Procurar", command=lambda: self.browse_directory(self.input_entry)).pack(side='right', padx=5)

        ttk.Label(self.basic_frame, text="Diretório de Saída:").pack(pady=5)
        output_frame = ttk.Frame(self.basic_frame)
        output_frame.pack(fill='x', padx=20)

        self.output_entry = ttk.Entry(output_frame)
        self.output_entry.pack(side='left', fill='x', expand=True)
        ttk.Button(output_frame, text="Procurar", command=lambda: self.browse_directory(self.output_entry)).pack(side='right', padx=5)

        settings_frame = ttk.Frame(self.basic_frame)
        settings_frame.pack(fill='x', padx=20, pady=10)

        settings_notebook = ttk.Notebook(settings_frame)
        settings_notebook.pack(fill='both', expand=True)

        settings_frame_size = ttk.Frame(settings_notebook)
        settings_frame_quality = ttk.Frame(settings_notebook)

        settings_notebook.add(settings_frame_size, text='Tamanho')
        settings_notebook.add(settings_frame_quality, text='Qualidade')

        width_frame = ttk.Frame(settings_frame_size)
        width_frame.pack(side='left', fill='x', expand=True, padx=5)
        ttk.Label(width_frame, text="Largura do Corte (px):").pack()
        self.width_var = tk.StringVar(value="")
        ttk.Entry(width_frame, textvariable=self.width_var).pack(fill='x')

        height_frame = ttk.Frame(settings_frame_size)
        height_frame.pack(side='right', fill='x', expand=True, padx=5)
        ttk.Label(height_frame, text="Altura do Corte (px):").pack()
        self.height_var = tk.StringVar(value="")
        ttk.Entry(height_frame, textvariable=self.height_var).pack(fill='x')

        quality_label = ttk.Label(settings_frame_quality, text="Qualidade da Imagem (%):")
        quality_label.pack(pady=5)
        self.quality_var = tk.StringVar(value="85")
        self.quality_spinbox = ttk.Spinbox(
            settings_frame_quality,
            from_=1,
            to=100,
            textvariable=self.quality_var,
            width=10
        )
        self.quality_spinbox.pack(pady=5)

        self.process_button = ttk.Button(self.basic_frame, text="Confirmar", command=lambda: threading.Thread(target=self.start_processing).start())
        self.process_button.pack(pady=20)

        self.progress = ttk.Progressbar(self.basic_frame, variable=self.progress_var, maximum=100, orient='horizontal', length=200, mode='determinate')
        self.progress.pack(fill='x', padx=20, pady=5)

        # Novo CustomLogFrame
        self.log_frame = CustomLogFrame(self.basic_frame)
        self.log_frame.pack(fill='x', padx=20, pady=10)
        
        
         # Chamar os métodos para configurar as outras abas
        self.setup_converter_gui()
        self.setup_comprimir_gui()
        
    def setup_converter_gui(self):
        # Frame principal para conversão
        converter_main_frame = ttk.Frame(self.converter_frame)
        converter_main_frame.pack(padx=10, pady=10, fill='both', expand=True)

        # Diretório de entrada
        input_frame = ttk.Frame(converter_main_frame)
        input_frame.pack(fill='x', padx=10, pady=5)
    
        ttk.Label(input_frame, text="Diretório de Entrada:").pack(side='left')
        self.converter_input_entry = ttk.Entry(input_frame, width=50)
        self.converter_input_entry.pack(side='left', expand=True, fill='x', padx=5)
    
        ttk.Button(input_frame, text="Procurar", 
                   command=lambda: self.browse_directory(self.converter_input_entry)).pack(side='right')

        # Seleção de formato de saída
        format_frame = ttk.Frame(converter_main_frame)
        format_frame.pack(fill='x', padx=10, pady=5)
    
        ttk.Label(format_frame, text="Formato de Saída:").pack(side='left')
        self.converter_format_var = tk.StringVar(value='jpeg')
        format_options = ['jpeg', 'jpg', 'png', 'webp']
    
        converter_format_dropdown = ttk.Combobox(
            format_frame, 
                textvariable=self.converter_format_var, 
            values=format_options,
            state='readonly',
            width=10
        )
        converter_format_dropdown.pack(side='left', padx=5)

        # Botão de conversão
        convert_button = ttk.Button(
            converter_main_frame, 
            text="Converter Imagens", 
            command=self.convert_images
        )
        convert_button.pack(pady=10)
        
        # Caixa de aviso
        messagebox.showwarning("Informação", "O limite de tamanho de altura do Webp não pode exceder 16383 pixeis utilizando a pagina converter")

        # Frame de log para conversão
        self.converter_log_frame = CustomLogFrame(self.converter_frame, height=3)
        self.converter_log_frame.pack(fill='x', padx=10, pady=5)

    def convert_images(self):
        # Obter diretório de entrada
        input_directory = self.converter_input_entry.get()

        # Obter formato de saída
        output_format = self.converter_format_var.get()

        # Validar entrada
        if not input_directory:
            self.converter_log_frame.update_log("Selecione um diretório de entrada", "ERROR")
            return

        # Função para executar a conversão
        def run_conversion():
            try:
                # Passar o método update_log como callback
                conversion.convert_images(
                   input_directory, 
                    output_format, 
                    log_callback=self.converter_log_frame.update_log
                )
            except Exception as e:
                self.root.after(0, lambda: self.converter_log_frame.update_log(
                    f"Erro na conversão: {str(e)}", "ERROR"
                ))

        # Criar e iniciar a thread
        conversion_thread = threading.Thread(
            target=run_conversion, 
            daemon=True
        )
        conversion_thread.start()
        
    
    def setup_comprimir_gui(self):
        # Frame principal para compressão
        compress_main_frame = ttk.Frame(self.comprimir_frame)
        compress_main_frame.pack(padx=10, pady=10, fill='both', expand=True)

        # Diretório de entrada para compressão
        input_frame = ttk.Frame(compress_main_frame)
        input_frame.pack(fill='x', padx=10, pady=5)
    
        ttk.Label(input_frame, text="Diretório de Entrada:").pack(side='left')
        self.compress_input_entry = ttk.Entry(input_frame, width=50)
        self.compress_input_entry.pack(side='left', expand=True, fill='x', padx=5)
    
        ttk.Button(input_frame, text="Procurar", 
                   command=lambda: self.browse_directory(self.compress_input_entry)).pack(side='right')

        # Opções de compressão
        options_frame = ttk.Frame(compress_main_frame)
        options_frame.pack(fill='x', padx=10, pady=5)

        # Checkbox para compressão recursiva
        self.recursive_compress_var = tk.BooleanVar(value=False)
        recursive_check = ttk.Checkbutton(
            options_frame, 
            text="Compressão Recursiva", 
            variable=self.recursive_compress_var
       )
        recursive_check.pack(side='left', padx=5)

        # Botão de compressão
        compress_button = ttk.Button(
            compress_main_frame, 
            text="Comprimir Imagens", 
            command=self.compress_images
       )
        compress_button.pack(pady=10)

        # Frame de log para compressão
        self.compress_log_frame = CustomLogFrame(self.comprimir_frame, height=3)
        self.compress_log_frame.pack(fill='x', padx=10, pady=5)

    def compress_images(self):
        # Obter diretório de entrada
        input_directory = self.compress_input_entry.get()
    
        # Validar entrada
        if not input_directory:
            self.compress_log_frame.update_log("Selecione um diretório de entrada", "ERROR")
            return
    
        # Função para executar a compressão em uma thread separada
        def run_compression():
            try:
                # Importar a função de compressão do módulo compress
                from compress import process_directory_recursive
             
                # Chamar a função de compressão com callback de log
                process_directory_recursive(
                    input_directory, 
                    log_callback=self.compress_log_frame.update_log
                )
            except Exception as e:
                # Atualizar log de erro na thread principal
                self.root.after(0, lambda: self.compress_log_frame.update_log(
                     f"Erro na compressão: {str(e)}", "ERROR"
                ))

        # Iniciar compressão em uma thread separada
        threading.Thread(target=run_compression, daemon=True).start()    
    

    def update_log(self, message):
        # Determinar o nível do log baseado no conteúdo da mensagem
        level = "INFO"
        if "erro" in message.lower() or "falha" in message.lower():
            level = "ERROR"
        elif "concluído" in message.lower() or "sucesso" in message.lower():
            level = "SUCCESS"
        elif "aviso" in message.lower() or "atenção" in message.lower():
            level = "WARNING"
        
        self.log_frame.update_log(message, level)

    def browse_directory(self, entry):
        directory = filedialog.askdirectory()
        if directory:
            entry.delete(0, tk.END)
            entry.insert(0, directory)

    def update_progress(self, value):
        self.progress_var.set(value)
        self.root.update_idletasks()

    def start_processing(self):
        if self.is_processing:
            return

        input_dir = self.input_entry.get()
        output_dir = self.output_entry.get()

        if not input_dir or not output_dir:
            self.status_var.set("Selecione os diretórios de entrada e saída")
            return

        self.is_processing = True
        self.stop_flag = False
        self.process_button.config(state='disabled', text="Processando...")
        self.status_var.set("Processando imagens...")

        self.processor = ImageProcessor(self.logger)
        self.processing_thread = threading.Thread(target=self.process)
        self.processing_thread.start()

    def process(self):
        input_dir = self.input_entry.get()
        output_dir = self.output_entry.get()
        width = int(self.width_var.get()) if self.width_var.get() else 0
        height = int(self.height_var.get()) if self.height_var.get() else 0
        quality = int(self.quality_var.get()) if self.quality_var.get() else 85

        try:
            self.processor.process_images(
                input_dir, output_dir, width, height, None, self.update_progress, quality
            )
            if not self.stop_flag:
                self.root. after(0, self.processing_complete)
        except Exception as e:
            self.root.after(0, lambda: self.processing_error(str(e)))

    def processing_complete(self):
        self.is_processing = False
        self.process_button.config(state='normal', text="Confirmar")
        self.status_var.set("Processamento concluído")
        self.progress_var.set(100)

    def processing_error(self, error_message):
        self.is_processing = False
        self.process_button.config(state='normal', text="Confirmar")
        self.status_var.set(f"Erro: {error_message}")

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = ImageProcessorGUI()
    app.run()
