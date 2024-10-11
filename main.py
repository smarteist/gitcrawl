import argparse
import os
import csv
from git import Repo


def save_diff_to_file(diff, filepath):
    with open(filepath, 'w') as file:
        file.write(str(diff))


def main(repo_path, keywords, file_extensions, buggy_dir, fixed_dir):
    if repo_path.startswith('http://') or repo_path.startswith('https://'):
        repo_dir = repo_path.split('/')[-1]
        if not os.path.exists(repo_dir):
            Repo.clone_from(repo_path, repo_dir)
        repo = Repo(repo_dir)
    else:
        repo = Repo(repo_path)

    keywords = [keyword.lower() for keyword in keywords.split(',')]
    file_extensions = file_extensions.split(',')

    for commit in repo.iter_commits():
        if any(keyword in commit.message.lower() for keyword in keywords):
            print(f'Commit ID: {commit.hexsha}, Message: {commit.message}')
            stats = commit.stats

            # Create directories for each commit
            buggy_commit_dir = os.path.join(buggy_dir, commit.hexsha)
            fixed_commit_dir = os.path.join(fixed_dir, commit.hexsha)
            os.makedirs(buggy_commit_dir, 0o755, True)
            os.makedirs(fixed_commit_dir, 0o755, True)

            # Save CSV in the fixed directory
            output_csv = os.path.join(fixed_commit_dir, 'commit_info.csv')
            with open(output_csv, 'w', newline='') as csvfile:
                fieldnames = ['commit_id', 'commit_message', 'file', 'relative_directory', 'lines_added',
                              'lines_deleted', 'change_type', 'author_name', 'author_email', 'commit_date']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()

                print('Files changed:')
                for file in stats.files:
                    if any(file.endswith(ext) for ext in file_extensions):
                        print(file)

                        diff_index = commit.parents[0].diff(commit)
                        for diff in diff_index.iter_change_type('M'):
                            if diff.a_path == file or diff.b_path == file:
                                print(f'Differences in {file}:')
                                print(diff)

                                file_base_name = os.path.basename(file)
                                file_relative_dir = os.path.dirname(file)

                                buggy_path = os.path.join(buggy_commit_dir, f'{file_base_name}')
                                fixed_path = os.path.join(fixed_commit_dir, f'{file_base_name}')

                                save_diff_to_file(diff.a_blob.data_stream.read().decode('utf-8'), buggy_path)
                                save_diff_to_file(diff.b_blob.data_stream.read().decode('utf-8'), fixed_path)

                                # Write information to CSV
                                writer.writerow({
                                    'commit_id': commit.hexsha,
                                    'commit_message': commit.message,
                                    'file': file,
                                    'relative_directory': file_relative_dir,
                                    'lines_added': diff.added,
                                    'lines_deleted': diff.deleted,
                                    'change_type': diff.change_type,
                                    'author_name': commit.author.name,
                                    'author_email': commit.author.email,
                                    'commit_date': commit.committed_datetime
                                })


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Search for specific keywords in git commits.')
    parser.add_argument('-r', '--repo_path', type=str,
                        help='Path to the local git repository or URL of the git repository')
    parser.add_argument('-k', '--keywords', type=str, help='Comma-separated keywords to search for in commit messages')
    parser.add_argument('-e', '--file_extensions', type=str,
                        help='Comma-separated file extensions to filter changes for')
    parser.add_argument('-b', '--buggy_dir', type=str, help='Directory to save buggy code diffs',
                        default=os.path.join(os.path.dirname(__file__), 'bugs'))
    parser.add_argument('-f', '--fixed_dir', type=str, help='Directory to save fixed code diffs',
                        default=os.path.join(os.path.dirname(__file__), 'fixes'))

    args = parser.parse_args()
    main(args.repo_path, args.keywords, args.file_extensions, args.buggy_dir, args.fixed_dir)
