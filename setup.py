from setuptools import setup, find_packages

setup(
    name="manytasks",
    version="1.0",
    keywords=["manytasks", ],
    description="eds sdk",
    long_description="A tool for deploying many tasks automatically.",
    license="WTFPL Licence",

    url="https://github.com/dugu9sword/manytasks",
    author="dugu9sword",
    author_email="dugu9sword@163.com",

    packages=find_packages(),
    include_package_data=True,
    platforms="any",
    install_requires=[
        "colorama",
        "flask",
        "nvidia-ml-py3",
        "tailer",
        "hjson",
        "tabulate"
    ],
    zip_safe=False,

    scripts=[],
    entry_points={
        'console_scripts': [
            'manytasks = manytasks.run_task:main'
        ]
    }
)
