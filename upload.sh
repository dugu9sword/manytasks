python setup.py sdist bdist_wheel
twine check dist/*
python -m twine upload --repository-url https://upload.pypi.org/legacy/ dist/*
