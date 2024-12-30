import os
from pathlib import Path
from typing import Dict, Optional, Callable
from PIL import Image
from concurrent.futures import ThreadPoolExecutor
from collections import defaultdict
import time
import logging
import argparse
import logging
import time

class GuiLoggingHandler(logging.Handler):
    def __init__(self, update_func):
        super().__init__()
        self.update_func = update_func

    def emit(self, record):
        # Obtém a mensagem do log
        log_message = self.format(record)
        # Chama a função de atualização na GUI com o log
        self.update_func(log_message)

class ImageProcessor:
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)
        self.supported_formats = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.gif', '.webp'}

    def find_image_files(self, input_folder: str):
        """Mapeia todas as imagens e suas localizações."""
        self.logger.info(f"Iniciando mapeamento de imagens no diretório: {input_folder}")
        images = {}
        for root, _, files in os.walk(input_folder):
            for file in files:
                if Path(file).suffix.lower() in self.supported_formats:
                    relative_path = Path(root).relative_to(input_folder)
                    if relative_path not in images:
                        images[relative_path] = []
                    images[relative_path].append(Path(root) / file)
        total_images = sum(len(files) for files in images.values())
        self.logger.info(f"Total de imagens encontradas: {total_images}")
        return images

    def process_images(self, input_folder: str, output_folder: str, width: int, slice_height: int):
        """Processa imagens com redimensionamento, montagem e fatiamento."""
        images_map = self.find_image_files(input_folder)
        total_images = sum(len(files) for files in images_map.values())

        if total_images == 0:
            self.logger.info("Nenhuma imagem encontrada para processar.")
            return

        os.makedirs(output_folder, exist_ok=True)

        processed_count = 0
        start_time = time.time()

        for relative_path, files in images_map.items():
            output_path = Path(output_folder) / relative_path
            output_path.mkdir(parents=True, exist_ok=True)

            with ThreadPoolExecutor(max_workers=4) as executor:  # Limite de threads
                def process_file(file):
                    with Image.open(file) as img:  # Context manager para abrir imagens
                        resized_img = img.resize((width, int((width / img.width) * img.height)), Image.Resampling.LANCZOS)
                        return resized_img

                resized_images = list(executor.map(process_file, files))

            total_height = sum(img.height for img in resized_images)
            strip = Image.new('RGB', (width, total_height))

            current_height = 0
            for img in resized_images:
                strip.paste(img, (0, current_height))
                current_height += img.height

            # Fatiar a tira
            for i in range(0, strip.height, slice_height):
                box = (0, i, strip.width, min(i + slice_height, strip.height))
                slice_image = strip.crop(box)

                # Manter o formato original
                format_ = files[0].suffix.lower().replace('.', '').upper()
                if format_ not in ['JPEG', 'PNG', 'WEBP']:
                    self.logger.warning(f"Formato não suportado: {format_}. Usando JPEG como padrão.")
                    format_ = 'JPEG'
                slice_file = output_path / f"slice_{i // slice_height}.{format_.lower()}"
                self._save_image(slice_image, slice_file, format_)

            processed_count += len(files)

            # Log progress periodicamente
            if processed_count % 10 == 0 or processed_count == total_images:
                self.logger.info(f"Processado: {processed_count}/{total_images} imagens")

        end_time = time.time()
        self.logger.info(f"Processamento concluído em {end_time - start_time:.2f} segundos")

    def _save_image(self, image: Image.Image, file_path: Path, format_: str):
        """Salva a imagem com compressão, mantendo a qualidade."""
        self.logger.info(f"Iniciando salvamento da imagem: {file_path}")
        try:
            if format_ == 'JPEG':
                image = image.convert('RGB')
                image.save(file_path, format_, quality=85, optimize=True, progressive=True)
            elif format_ == 'PNG':
                image.save(file_path, format_, optimize=True, compress_level=9)
            elif format_ == 'WEBP':
                image.save(file_path, format_, quality=85, optimize=True)
            else:
                image.save(file_path, format_)

            self.logger.info(f"Imagem salva: {file_path}")
        except Exception as e:
            self.logger.error(f"Erro ao salvar imagem {file_path}: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Processador de Imagens")
    parser.add_argument("input_dir", type=str, help="Diretório de entrada com imagens")
    parser.add_argument("output_dir", type=str, help="Diretório de saída para imagens processadas")
    parser.add_argument("--width", type=int, default=800, help="Largura-alvo para redimensionamento das imagens")
    parser.add_argument("--slice_height", type=int, default=600, help="Altura de fatiamento das imagens")

    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)
    processor = ImageProcessor()

    processor.process_images(args.input_dir, args.output_dir, args.width, args.slice_height)
