import zipfile,os
from datetime import datetime
from configparser import ConfigParser
from pathlib import Path
import subprocess
from concurrent.futures import ThreadPoolExecutor


def zipdir(dir_path, ziph):
    for root, dirs, files in os.walk(dir_path):
        for file in files:
            file_path = os.path.join(root, file)
            arcname = os.path.relpath(file_path, dir_path)
            ziph.write(file_path, arcname=arcname)


def main():
    # Load configuration file
    config = ConfigParser()
    config.read('config.ini')

    # Read list of directories to archive from configuration file
    dirs = config.items('directories')

    # Read password for encryption from configuration file
    password = config.get('encryption', 'password')

    # datetime object containing current date and time
    now = datetime.now()
    # dd/mm/YY H:M:S
    datetime_str = now.strftime("%Y%m%d%H%M")

    # Create a new zip archive file
    zip_file_path = Path(f"Backup_{datetime_str}.zip")
    with zipfile.ZipFile(zip_file_path, 'w', compression=zipfile.ZIP_DEFLATED) as zip_file:
        zip_file.setpassword(password.encode())  # Set password for encryption

        # Iterate over each directory and add its files to the zip archive
        with ThreadPoolExecutor() as executor:
            for _, dir_path in dirs:
                executor.submit(zipdir, dir_path, zip_file)

    # Processing with Encryption zip file
    subprocess.run(["openssl", "enc", "-aes-256-cbc", "-pbkdf2", "-in", zip_file_path,
                    "-out", f"{zip_file_path}.enc", "-k", password], check=True)
    os.remove(zip_file_path)

    # Print a message indicating that the archive was created successfully
    print("Archive created successfully!")


if __name__ == '__main__':
    main()
