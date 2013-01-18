import os

exclude_dirs = ['.git']
exclude_files = ['.gitignore']

package_files = []
for root, dirs, files in os.walk('graphdat/lib'):
	files[:] = [f for f in files if f not in exclude_files]
	dirs[:] = [d for d in dirs if d not in exclude_dirs]
	package_files += ['%s/%s' % (root[9:], file) for file in files]

print package_files
