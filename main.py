import argparse
import os
from git import Repo


def save_diff_to_file(diff, filepath):
    with open(filepath, 'w') as file:
        file.write(str(diff))


def main(repo_path, keywords, file_extension, buggy_dir, fixed_dir):
    if repo_path.startswith('http://') or repo_path.startswith('https://'):
        repo_dir = repo_path.split('/')[-1]
        if not os.path.exists(repo_dir):
            Repo.clone_from(repo_path, repo_dir)
        repo = Repo(repo_dir)
    else:
        repo = Repo(repo_path)

    keywords = [keyword.lower() for keyword in keywords.split(',')]

    for commit in repo.iter_commits():
        if any(keyword in commit.message.lower() for keyword in keywords):
            print(f'Commit ID: {commit.hexsha}, Message: {commit.message}')
            stats = commit.stats

            print('Files changed:')
            for file in stats.files:
                if file.endswith(file_extension):
                    print(file)

                    diff_index = commit.parents[0].diff(commit)
                    for diff in diff_index.iter_change_type('M'):
                        if diff.a_path == file or diff.b_path == file:
                            print(f'Differences in {file}:')
                            print(diff)

                            file_base_name = os.path.splitext(os.path.basename(file))[0]

                            buggy_path = os.path.join(buggy_dir, f'{file_base_name}_{commit.hexsha}_buggy.diff')
                            fixed_path = os.path.join(fixed_dir, f'{file_base_name}_{commit.hexsha}_fixed.diff')

                            save_diff_to_file(diff.a_blob.data_stream.read().decode('utf-8'), buggy_path)
                            save_diff_to_file(diff.b_blob.data_stream.read().decode('utf-8'), fixed_path)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Search for specific keywords in git commits.')
    parser.add_argument('-r', '--repo_path', type=str,
                        help='Path to the local git repository or URL of the git repository')
    parser.add_argument('-k', '--keywords', type=str, help='Comma-separated keywords to search for in commit messages')
    parser.add_argument('-e', '--file_extension', type=str, help='File extension to filter changes for')
    parser.add_argument('-b', '--buggy_dir', type=str, help='Directory to save buggy code diffs',
                        default=os.path.join(os.path.dirname(__file__), 'bugs'))
    parser.add_argument('-f', '--fixed_dir', type=str, help='Directory to save fixed code diffs',
                        default=os.path.join(os.path.dirname(__file__), 'fixes'))

    args = parser.parse_args()
    main(args.repo_path, args.keywords, args.file_extension, args.buggy_dir, args.fixed_dir)
