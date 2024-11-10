import os


def get_files_under_dir(dir_path):
    # check if path is directory
    if not os.path.isdir(dir_path):
        return None
    # List all .xls files
    xls_files = [f for f in os.listdir(dir_path) if f.endswith('.xls')]
    return xls_files
