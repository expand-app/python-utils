from setuptools import setup, find_packages


def get_version_info(file_path='./python_utils/__init__.py'):
    """
    Reads a Python file and extracts the version information.

    :param file_path: The path to the file from which to extract the version info.
    :return: The version string if found, otherwise None.
    """
    try:
        with open(file_path, 'r') as file:
            for line in file:
                # Check if the line contains the version info
                if line.strip().startswith('__version__'):
                    # Extract and return the version string
                    return line.split('=')[1].strip().strip('"').strip("'")
    except FileNotFoundError:
        print(f"The file {file_path} was not found.")
        return None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None


setup(
    name='python-utils',
    version=get_version_info(),
    author='Shuo Feng',
    author_email='shuo.s.feng@gmail.com',
    packages=find_packages(),
    license='MIT',
    description='Python utilities',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    install_requires=[
        'openpyxl', 'pandas', 'requests', 'setuptools'
    ],
    python_requires='>=3.11',
)
