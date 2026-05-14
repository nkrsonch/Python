import argparse
import logging
import os
import time


LOG_FILENAME = 'clean_trash.log'


def setup_logging():
    logging.basicConfig(
        filename=LOG_FILENAME,
        level=logging.INFO,
        format='%(asctime)s %(message)s',
    )


def is_too_old(path, age_thr):
    age = time.time() - os.path.getmtime(path)
    return age > age_thr


def remove_old_files(trash_folder_path, age_thr):
    for root, dirs, files in os.walk(trash_folder_path):
        dirs[:] = sorted(dirs)

        for filename in sorted(files):
            file_path = os.path.join(root, filename)
            if os.path.exists(file_path) and is_too_old(file_path, age_thr):
                os.remove(file_path)
                logging.info('Removed file: %s', file_path)


def remove_empty_directories(trash_folder_path):
    for root, dirs, files in os.walk(trash_folder_path, topdown=False):
        if root == trash_folder_path:
            continue

        if os.path.exists(root) and not os.listdir(root):
            os.rmdir(root)
            logging.info('Removed directory: %s', root)


def clean_trash(trash_folder_path, age_thr):
    remove_old_files(trash_folder_path, age_thr)
    remove_empty_directories(trash_folder_path)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--trash_folder_path', type=str, required=True)
    parser.add_argument('--age_thr', type=float, required=True)
    args = parser.parse_args()

    setup_logging()

    while True:
        clean_trash(args.trash_folder_path, args.age_thr)
        time.sleep(1)


if __name__ == '__main__':
    main()
