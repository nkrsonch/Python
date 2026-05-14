import argparse
import os
import re


def read_ignore_rules(project_dir):
    gitignore_path = os.path.join(project_dir, '.gitignore')
    with open(gitignore_path, encoding='utf-8-sig') as gitignore_file:
        return [
            line.strip()
            for line in gitignore_file
            if line.strip()
        ]


def normalize_path(path):
    return path.replace(os.sep, '/')


def is_wildcard_match(rule, relative_path):
    filename = os.path.basename(relative_path)
    pattern = '^' + re.escape(rule).replace('\\*', '.*') + '$'
    return re.match(pattern, filename) is not None


def collect_project_files(project_dir):
    project_files = []

    for root, dirs, files in os.walk(project_dir):
        dirs[:] = sorted(dirname for dirname in dirs if dirname != '.git')

        for filename in sorted(files):
            file_path = os.path.join(root, filename)
            relative_path = normalize_path(os.path.relpath(file_path, project_dir))
            project_files.append(relative_path)

    return project_files


def find_ignored_files(project_dir, rules):
    project_files = collect_project_files(project_dir)
    ignored_files = []
    reported_files = set()

    for rule in rules:
        normalized_rule = normalize_path(rule)

        for relative_path in project_files:
            if relative_path in reported_files:
                continue

            if rule.startswith('*'):
                matches = is_wildcard_match(rule, relative_path)
            else:
                matches = relative_path == normalized_rule

            if matches:
                ignored_files.append((relative_path, rule))
                reported_files.add(relative_path)

    return ignored_files


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--project_dir', type=str, required=True)
    args = parser.parse_args()

    rules = read_ignore_rules(args.project_dir)
    ignored_files = find_ignored_files(args.project_dir, rules)

    print('Ignored files:')
    for file_path, rule in ignored_files:
        print(f'{file_path} ignored by expression {rule}')


if __name__ == '__main__':
    main()
