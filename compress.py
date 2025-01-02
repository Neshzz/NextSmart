import os
from PIL import Image, UnidentifiedImageError
from concurrent.futures import ThreadPoolExecutor
from collections import defaultdict
import sys

def print_progress_bar(progress, total, prefix='', suffix='', length=50):
    percentage = 100 * (progress / total)
    filled_length = int(length * progress // total)
    bar = '=' * filled_length + '-' * (length - filled_length)
    sys.stdout.write(f'\r{prefix} |{bar}| {percentage:.2f}% {suffix}')
    sys.stdout.flush()
    if progress == total:
        sys.stdout.write('\n')

def compress_image(file_path, output_directory):
    try:
        # Tenta abrir a imagem
        img = Image.open(file_path)

        # Cria o caminho para salvar a imagem comprimida
        output_file_path = os.path.join(
            output_directory, os.path.basename(file_path)
        )

        # Determina o formato com base na extensão original
        format_ = img.format if img.format in ['JPEG', 'PNG', 'WEBP'] else 'JPEG'

        # Comprime a imagem dependendo do formato
        if format_ == 'JPEG':
            img = img.convert('RGB')  # Garante compatibilidade para JPEG
            img.save(output_file_path, format_, quality=85, optimize=True, progressive=True)
        elif format_ == 'PNG':
            img.save(output_file_path, format_, optimize=True, compress_level=9)
        elif format_ == 'WEBP':
            img.save(output_file_path, format_, quality=85, optimize=True)

        return os.path.basename(file_path), True
    except Exception as e:
        return os.path.basename(file_path), False

def compress_images_in_directory(directory, output_base_directory, progress_data):
    supported_formats = ('.jpeg', '.jpg', '.png', '.bmp', '.gif', '.webp')

    # Caminho da pasta de saída
    os.makedirs(output_base_directory, exist_ok=True)

    # Filtra apenas arquivos de imagem suportados
    files = [
        f for f in os.listdir(directory)
        if os.path.isfile(os.path.join(directory, f)) and f.lower().endswith(supported_formats)
    ]

    if not files:
        return 0, defaultdict(int)  # Nenhuma imagem encontrada

    total_images_compressed = 0
    image_count_by_extension = defaultdict(int)

    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = []
        for filename in files:
            file_path = os.path.join(directory, filename)
            futures.append(executor.submit(compress_image, file_path, output_base_directory))

        for future in futures:
            result = future.result()
            if result[1]:
                image_count_by_extension[os.path.splitext(result[0])[1].lower()] += 1
                total_images_compressed += 1
            progress_data["progress"] += 1
            print_progress_bar(progress_data["progress"], progress_data["total"], prefix="Progresso Geral", suffix="Completado", length=50)

    return total_images_compressed, image_count_by_extension

def process_directory_recursive(base_directory, log_callback=None):
    base_directory = base_directory.strip('"')

    if not os.path.exists(base_directory):
        if log_callback:
            log_callback(f"O diretório '{base_directory}' não existe.", "ERROR")
        return

    total_compressed = 0
    overall_image_count_by_extension = defaultdict(int)

    # Calcula o número total de arquivos para a barra de progresso geral
    total_files = sum(
        len([f for f in files if f.lower().endswith(('.jpeg', '.jpg', '.png', '.bmp', '.gif', '.webp'))])
        for _, _, files in os.walk(base_directory)
    )

    progress_data = {"progress": 0, "total": total_files}

    # Caminha pela estrutura de diretórios
    for root, dirs, files in os.walk(base_directory):
        relative_path = os.path.relpath(root, base_directory)
        output_base_directory = os.path.join(base_directory + "-optimized", relative_path)

        os.makedirs (output_base_directory, exist_ok=True)

        # Comprime as imagens no diretório atual
        compressed, image_count_by_extension = compress_images_in_directory(root, output_base_directory, progress_data)

        total_compressed += compressed
        for ext, count in image_count_by_extension.items():
            overall_image_count_by_extension[ext] += count

        # Atualizar log após cada diretório processado
        if log_callback:
            log_callback(f"Diretório processado: {relative_path}, Total comprimido: {compressed}", "INFO")

    # Exibe o relatório final
    if log_callback:
        log_callback("\n--- Compressão Concluída ---", "INFO")
        log_callback(f"Total de imagens comprimidas: {total_compressed}", "SUCCESS")
        log_callback("Quantidade por tipo de imagem:", "INFO")
        for ext, count in overall_image_count_by_extension.items():
            log_callback(f"{ext}: {count}", "INFO")

def main():
    base_directory = input("Insira o diretório base das imagens: ")
    process_directory_recursive(base_directory)

if __name__ == "__main__":
    main()