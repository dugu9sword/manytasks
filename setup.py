from setuptools import setup, find_packages
from pathlib import Path

this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()

setup(
    name="manytasks",
    version="2.2",
    keywords=["manytasks", ],
    description="A tool for deploying many tasks automatically.",
    long_description=long_description,
    long_description_content_type='text/markdown',
    license="WTFPL Licence",

    url="https://github.com/dugu9sword/manytasks",
    author="dugu9sword",
    author_email="dugu9sword@163.com",

    packages=find_packages(),
    include_package_data=True,
    platforms="any",
    install_requires=open("requirements.txt").readlines(),
    zip_safe=False,

    scripts=[],
    entry_points={
        'console_scripts': [
            'manytasks = manytasks.entry:main',
        ]
    }
)
