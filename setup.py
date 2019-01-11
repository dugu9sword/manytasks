from setuptools import setup, find_packages

setup(
    name="alchemist",
    version="20190101",
    keywords=["alchemist", ],
    description="eds sdk",
    long_description="A toy tool for deep learning, which helps explore different net configurations.",
    license="WTFPL Licence",

    url="https://github.com/dugu9sword/alchemist",
    author="dugu9sword",
    author_email="dugu9sword@163.com",

    packages=find_packages(),
    include_package_data=True,
    platforms="any",
    install_requires=[
        "colorama",
        "flask",
        "nvidia-ml-py3",
        "tailer"
    ],
    zip_safe=False,

    scripts=[],
    entry_points={
        'console_scripts': [
            'alchemist = alchemist.run_task:main'
        ]
    }
)
