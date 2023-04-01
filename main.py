import os
import zipfile
from datetime import datetime
from configparser import ConfigParser


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
    with zipfile.ZipFile("Backup_" + datetime_str + ".zip", 'w', compression=zipfile.ZIP_DEFLATED) as zip_file:
        zip_file.setpassword(password.encode())  # Set password for encryption

        # Iterate over each directory and add its files to the zip archive
        for dir_, dir_name in dirs:
            print(dir_name)
            for root, _, files in os.walk(dir_name):
                # for root, _, files in os.walk('/home/jerryw/Downloads'):
                print(root, _)
                for file in files:
                    print(file)
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, os.path.dirname(dir_name))
                    zip_file.write(file_path, arcname=arcname)

    # Print a message indicating that the archive was created successfully
    print("Archive created successfully!")
    # Processing with Encryption zip file
    command = "openssl enc -aes-256-cbc -pbkdf2 -in Backup_" + datetime_str + ".zip -out Backup_" + datetime_str + ".zip.enc -k " + password
    os.system(command)
    os.remove("Backup_" + datetime_str + ".zip")

if __name__ == '__main__':
    main()
