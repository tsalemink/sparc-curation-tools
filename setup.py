import io

from setuptools import setup, find_packages


def readfile(filename, split=False):
    with io.open(filename, encoding="utf-8") as stream:
        if split:
            return stream.read().split("\n")
        return stream.read()


readme = readfile("README.rst", split=True)
readme.append('License')
readme.append('=======')
readme.append('')
readme.append('::')
readme.append('')
readme.append('')

software_licence = readfile("LICENSE")

requires = ['pandas', 'openpyxl']

setup(
    name='sparc-curation-tools',
    version='1.0.0',
    description='A collection of tools to help with curating SPARC datasets..',
    long_description='\n'.join(readme) + software_licence,
    long_description_content_type='text/x-rst',
    classifiers=[],
    author='Hugh Sorby',
    author_email='h.sorby@auckland.ac.nz',
    url='https://github.com/hsorby/sparc-curation-tools.git',
    license='Apache Software License',
    license_files=("LICENSE",),
    packages=find_packages("src"),
    package_dir={"": "src"},
    include_package_data=True,
    zip_safe=False,
    install_requires=requires,
)