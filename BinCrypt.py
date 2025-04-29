import sys
import os
from tqdm import tqdm
from typing import Optional, List, Tuple

def open_file(file_path: str) -> str:
    try:
        with open(file_path, 'r', encoding='ascii') as file:
            return file.read()
    except FileNotFoundError:
        print(f"Errno: File '{file_path}' not found")
        sys.exit(1)
    except UnicodeDecodeError:
        print(f"Errno: File '{file_path}' isnt a valid ASCII text file")
        sys.exit(1)

def save_file(content: str, file_path: str) -> None:
    if not file_path:
        print("Errno: .o file path cant be empty")
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

def _process_binary_chunk(chunk: str, bit_length: int) -> Tuple[Optional[str], Optional[str]]:
    if len(chunk) != bit_length:
        return None, f"Skipped incomplete chunk: {chunk}"
    if not all(c in '01' for c in chunk):
        return None, f"Invalid binary chunk: {chunk}"
    try:
        dec = int(chunk, 2)
        return chr(dec), None
    except ValueError:
        return None, f"Invalid binary chunk: {chunk}"

def deconvert_binary(input_path: str) -> str:
    try:
        text = ''
        errors = []
        file_size = os.path.getsize(input_path)
        with open(input_path, 'r', encoding='ascii') as f, \
             tqdm(total=file_size, unit='B', unit_scale=True, desc="Deconverting") as pbar:
            for line in f:
                binary_str = line.strip().replace(' ', '')
                if not all(c in '01' for c in binary_str):
                    errors.append(f"Invalid char in line: {line.strip()}")
                    continue
                if len(binary_str) % 8 != 0:
                    errors.append(f"Incomplete binary len line: {line.strip()}")
                for i in range(0, len(binary_str), 8):
                    chunk = binary_str[i:i+8]
                    char, error = _process_binary_chunk(chunk, bit_length=8)
                    if char:
                        text += char
                    if error:
                        errors.append(error)
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

def _split_byte(byte: int) -> Tuple[str, str]:
    last_bit = byte & 1  
    seven_bits = byte >> 1  
    return format(seven_bits, '07b'), str(last_bit)

def encrypt(input_path: str, output_path: Optional[str] = None, spacing: bool = True, 
            chunk_size: int = 4096) -> None:
    output_path = output_path or f"{input_path}.bin"
    key_path = f"{os.path.splitext(output_path)[0]}_key.bin"
    
    try:
        file_size = os.path.getsize(input_path)
        with open(input_path, 'rb') as f_in, \
             open(output_path, 'w', encoding='ascii') as f_out, \
             open(key_path, 'w', encoding='ascii') as f_key, \
             tqdm(total=file_size, unit='B', unit_scale=True, desc="Encrypting") as pbar:
            
            while True:
                chunk = f_in.read(chunk_size)
                if not chunk:
                    break
                
                binary_list = []
                key_bits = []
                for byte in chunk:
                    binary_str, key_bit = _split_byte(byte)
                    binary_list.append(binary_str)
                    key_bits.append(key_bit)
                
                separator = ' ' if spacing else ''
                f_out.write(separator.join(binary_list) + '\n')
                f_key.write(''.join(key_bits) + '\n')
                pbar.update(len(chunk))
                
        print(f"Saved 7-bit binary to {output_path}")
        print(f"Saved key bits to {key_path}")
    
    except FileNotFoundError:
        print(f"Errno: File '{input_path}' not found")
        sys.exit(1)
    except PermissionError:
        print(f"Errno: Permission denied")
        sys.exit(1)
    except Exception as e:
        print(f"Errno: {str(e)}")
        sys.exit(1)

def decrypt(input_path: str, key_path: str, output_path: Optional[str] = None) -> str:
    try:
        text = ''
        errors = []
        file_size = os.path.getsize(input_path)
        key_size = os.path.getsize(key_path)
        
        with open(input_path, 'r', encoding='ascii') as f_in, \
             open(key_path, 'r', encoding='ascii') as f_key, \
             tqdm(total=file_size, unit='B', unit_scale=True, desc="Decrypting") as pbar:
            
            key_lines = f_key.readlines()
            key_bits = ''.join(line.strip() for line in key_lines)
            key_index = 0
            
            for line in f_in:
                binary_str = line.strip().replace(' ', '')
                if not all(c in '01' for c in binary_str):
                    errors.append(f"Invalid char in line: {line.strip()}")
                    continue
                if len(binary_str) % 7 != 0:
                    errors.append(f"Incomplete binary len line: {line.strip()}")
                
                for i in range(0, len(binary_str), 7):
                    if key_index >= len(key_bits):
                        errors.append("Ran out of key bits")
                        break
                    chunk = binary_str[i:i+7]
                    char, error = _process_binary_chunk(chunk, bit_length=7)
                    if error:
                        errors.append(error)
                        continue
                    if char:
                        seven_bits = ord(char)  
                        last_bit = int(key_bits[key_index])  
                        full_byte = (seven_bits << 1) | last_bit  
                        text += chr(full_byte)
                        key_index += 1
                pbar.update(len(line.encode('ascii')))
        
        if errors:
            print(f"Processed with {len(errors)} errors:")
            for error in errors:
                print(error)
                
        if output_path:
            save_file(text, output_path)
        
        return text
    
    except FileNotFoundError as e:
        print(f"Errno: File not found: {e.filename}")
        sys.exit(1)
    except Exception as e:
        print(f"Errno decrypt: {str(e)}")
        return ''

def main():
    if len(sys.argv) < 3:
        print("!Usage: python bincrypt.py [--convert|--deconvert|--encrypt|--key] input_file [output_file] [spacing=1 for convert/encrypt]")
        print("For --key: python bincrypt.py --key input_file key_file [output_file]")
        sys.exit(1)
    
    option = sys.argv[1]
    input_file = sys.argv[2]
    
    if option in ('-c', '--convert'):
        output_file = sys.argv[3] if len(sys.argv) > 3 else None
        spacing = bool(int(sys.argv[4])) if len(sys.argv) > 4 else True
        file_to_binary(input_file, output_file, spacing)
    elif option in ('-d', '--deconvert'):
        output_file = sys.argv[3] if len(sys.argv) > 3 else None
        output_path = output_file or f"{input_file}.txt"
        text_content = deconvert_binary(input_file)
        save_file(text_content, output_path)
    elif option in ('-e', '--encrypt'):
        output_file = sys.argv[3] if len(sys.argv) > 3 else None
        spacing = bool(int(sys.argv[4])) if len(sys.argv) > 4 else True
        encrypt(input_file, output_file, spacing)
    elif option in ('-k', '--key'):
        if len(sys.argv) < 4:
            print("Errno: --key requires a key file path")
            sys.exit(1)
        key_file = sys.argv[3]
        output_file = sys.argv[4] if len(sys.argv) > 4 else None
        output_path = output_file or f"{input_file}.decrypted.txt"
        decrypt(input_file, key_file, output_path)
    else:
        print(f"Errno: Invalid option '{option}'. Use --convert, --deconvert, --encrypt, or --key")
        sys.exit(1)

if __name__ == "__main__":
    main()