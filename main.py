import configparser, pyminizip, zipfile
import hashlib
import os
import pickle
from datetime import datetime
import subprocess,argparse
import platform

NAS_Root = "X:\\DailyBackup\\172.27.21.111\\"

def is_windows():
    return os.name == 'nt'



class File:
    def __init__(self, path):
        self.path = path
        self.name = os.path.basename(path)
        self.size = os.path.getsize(path) if os.access(path, os.R_OK) else 0
        self.created_date = datetime.fromtimestamp(os.path.getctime(path)) if os.access(path, os.R_OK) else None
        self.updated_date = datetime.fromtimestamp(os.path.getmtime(path)) if os.access(path, os.R_OK) else None
        self.hash = self.calculate_hash() if os.access(path, os.R_OK) else None
    def calculate_hash(self):
        BUF_SIZE = 65536
        sha256 = hashlib.sha256()
        if os.access(self.path, os.R_OK):
            with open(self.path, "rb") as f:
                while True:
                    data = f.read(BUF_SIZE)
                    if not data:
                        break
                    sha256.update(data)
            return sha256.hexdigest()
    def __eq__(self, other):
        if isinstance(other, File):
            return self.path == other.path
        return False
    def __hash__(self):
        return hash(self.path)

class Directory:
    def __init__(self, path):
        self.path = path
    def get_files(self):
        files = []
        for root, _, filenames in os.walk(self.path):
            for filename in filenames:
                filepath = os.path.join(root, filename)
                if os.access(filepath, os.R_OK):
                    file = File(filepath)
                    files.append(file)
        return files

def get_args():
    parser = argparse.ArgumentParser(description='Backup script.')
    parser.add_argument('-f', '--full', help='Perform full backup.', action='store_true')
    parser.add_argument('-u', '--update', help='Perform update backup.', action='store_true')
    args = parser.parse_args()
    return args
def save_data(file_data):
    with open(NAS_Root+"file_data.pkl", "wb") as f:
        pickle.dump(file_data, f)

def load_data():
    try:
        with open(NAS_Root+"file_data.pkl", "rb") as f:
            return pickle.load(f)
    except FileNotFoundError:
        return []

def compress_encrypt_files(files_list, zip_filename, password):
    if platform.system() == 'Windows':
        CHUNK_SIZE = 1000  # Adjust as needed
        for i in range(0, len(files_list), CHUNK_SIZE):
            chunk = files_list[i:i+CHUNK_SIZE]
            file_list_file = 'files_list.txt'
            with open(file_list_file, 'w', encoding='utf-8') as f:
                f.write('\n'.join(chunk))
            subprocess.run(['7z', 'a', '-p' + password, '-y', '-spf', '-scsUTF-8', zip_filename, '@files_list.txt'])
            if os.path.exists(file_list_file):
                os.remove(file_list_file)

    elif platform.system() == 'Linux':
        # In linux we can use the original approach
        subprocess.run(['zip', '-P', password, '-r', zip_filename] + files_list)

    else:
        raise Exception('Unsupported OS')

def get_directories_from_config():
    config = configparser.ConfigParser()
    config.read('config.ini')
    return [Directory(dirpath) for dirpath in config['directories'].values()]
def backup(backup_type):
    old_data = load_data()
    config = configparser.ConfigParser()
    config.read('config.ini')
    password = config.get('encryption', 'password')
    machine_name = config.get('backup_filename', 'machine')
    directories = get_directories_from_config()
    oper_list = []
    files=[]
    for directory in directories:
        files.extend(directory.get_files())
    if old_data is not None and all(isinstance(f, File) for f in old_data) and backup_type=='update':
        old_dict = {f.path: f.hash for f in old_data}
        new_dict = {f.path: f.hash for f in files}
        changed_files = {path: (old_dict[path], new_hash) for path, new_hash in new_dict.items() if
                         path in old_dict and old_dict[path] != new_hash}
        added_files = set(new_dict) - set(old_dict)
        # removed_files = set(old_dict) - set(new_dict)
        for file_path, (old_hash, new_hash) in changed_files.items():
            print(f"Changed file detected - {file_path}:\n\tOld hash: {old_hash}\n\tNew hash: {new_hash}")
            oper_list.append(File(file_path))
        for file_path in added_files:
            print(f"Added file detected - {file_path}:\n\tHash: {new_dict[file_path]}")
            oper_list.append(File(file_path))
        #            for file_path in removed_files:
        #                print(f"Removed file detected - {file_path}:\n\tHash: {old_dict[file_path]}")
        #                oper_list.append(File(file_path))
        if len(oper_list) > 0:
            zip_filename = f"{NAS_Root}{machine_name}_ADD_MODIFY_{datetime.now().strftime('%Y%m%d-%H%M')}.zip"
            files_list = [f.path for f in oper_list]
            compress_encrypt_files(files_list, zip_filename, password)
            oper_list.extend(old_data)  # renamed 'append' to 'extend'
        save_data(added_files)
    else:
        for file in files:
            print(f"Path: {file.path}")
            print(f"Name: {file.name}")
            print(f"Size: {file.size} bytes")
            print(f"Creation Date: {file.created_date.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"Last Updated: {file.updated_date.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"SHA-256 Hash: {file.hash}")
            print("=====================================")
        zip_filename = f"{NAS_Root}{machine_name}_FULL_{datetime.now().strftime('%Y%m%d-%H%M')}.zip"
        files_list = [f.path for f in files]
        compress_encrypt_files(files_list, zip_filename, password)
        #files=files.append(oper_list)
    save_data(files)

def main():
    args = get_args()
    if args.full:
        backup(backup_type='full')
    elif args.update:
        backup(backup_type='update')
    else:
        backup(backup_type='update')
        #print("No valid argument supplied. Use -f for full backup or -u for update backup.")
if __name__ == "__main__":
    main()
