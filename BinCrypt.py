import sys
import os
from tqdm import tqdm
from typing import Optional

def open_file(file_path: str) -> str:
    try:
        with open(file_path, 'r', encoding='ascii') as file:
            return file.read()
    except FileNotFoundError:
        print(f"Errno: File '{file_path}' not found")
        sys.exit(1)
    except UnicodeDecodeError:
        print(f"Errno: File '{file_path}' is not a valid text file")
        sys.exit(1)

def file_to_binary(input_path: str, output_path: Optional[str] = None, spacing: bool = True, 
                  chunk_size: int = 4096) -> None:
    output_path = output_path or f"{input_path}.bin"
    
    try:
        file_size = os.path.getsize(input_path)
        with open(input_path, 'rb') as f_in, \
             open(output_path, 'w', encoding='ascii') as f_out, \
             tqdm(total=file_size, unit='B', unit_scale=True, desc="Converting") as pbar:
            
            while True:
                chunk = f_in.read(chunk_size)
                if not chunk:
                    break
                
                binary_list = [format(byte, '08b') for byte in chunk]
                separator = ' ' if spacing else ''
                f_out.write(separator.join(binary_list) + '\n')
                pbar.update(len(chunk))
                
        print(f"Saved binary to {output_path}")
    
    except FileNotFoundError:
        print(f"Errno: File '{input_path}' not found")
        sys.exit(1)
    except PermissionError:
        print(f"Errno: Permission denied")
        sys.exit(1)
    except Exception as e:
        print(f"Errno: {str(e)}")
        sys.exit(1)

def deconvert_streaming(input_path: str) -> str:
    try:
        text = ''
        errors = []
        file_size = os.path.getsize(input_path)
        with open(input_path, 'r', encoding='ascii') as f, \
             tqdm(total=file_size, unit='B', unit_scale=True, desc="Deconverting") as pbar:
            for line in f:
                binary_str = line.strip().replace(' ', '')
                if not all(c in '01' for c in binary_str):
                    errors.append(f"Invalid characters in line: {line.strip()}")
                    continue
                if len(binary_str) % 8 != 0:
                    errors.append(f"Incomplete binary length in line: {line.strip()}")
                for i in range(0, len(binary_str), 8):
                    chunk = binary_str[i:i+8]
                    if len(chunk) != 8:
                        errors.append(f"Skipped incomplete chunk: {chunk}")
                        continue
                    try:
                        dec = int(chunk, 2)
                        text += chr(dec)
                    except ValueError:
                        errors.append(f"Invalid binary chunk: {chunk}")
                pbar.update(len(line.encode('ascii')))
        
        if errors:
            print(f"Processed with {len(errors)} errors:")
            for error in errors:
                print(error)
                
        return text
    
    except FileNotFoundError:
        print(f"Errno: File '{input_path}' not found")
        sys.exit(1)
    except Exception as e:
        print(f"Errno deconvert: {str(e)}")
        return ''

def save_file(content: str, file_path: str) -> None:
    if not file_path:
        print("Errno: Output file path cannot be empty")
        sys.exit(1)
    try:
        os.makedirs(os.path.dirname(file_path) or '.', exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Saved: {file_path}")
    except PermissionError:
        print(f"Errno: Permission denied for '{file_path}'")
        sys.exit(1)
    except Exception as e:
        print(f"Errno saving: {e}")
        sys.exit(1)

def main():
    if len(sys.argv) < 3:
        print("!Usage: python script.py [--convert OR --deconvert] input_file [output_file] [spacing=1 for convert only]")
        sys.exit(1)
    
    option = sys.argv[1]
    input_file = sys.argv[2]
    output_file = sys.argv[3] if len(sys.argv) > 3 else None
    
    if option in ('-c', '--convert'):
        spacing = bool(int(sys.argv[4])) if len(sys.argv) > 4 else True
        file_to_binary(input_file, output_file, spacing)
    elif option in ('-d', '--deconvert'):
        text_content = deconvert_streaming(input_file)
        output_path = output_file or f"{input_file}.txt"
        if not output_path:
            print("Errno: Output path cannot be empty")
            sys.exit(1)
        save_file(text_content, output_path)
    else:
        print(f"Errno: Invalid option '{option}'. Use --convert OR --deconvert")
        sys.exit(1)

if __name__ == "__main__":
    main()
