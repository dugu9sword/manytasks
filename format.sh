echo 'Running autoflake...'
autoflake --in-place --remove-all-unused-imports --ignore-init-module-imports --recursive manytasks/

echo 'Running isort ...'
isort manytasks/*.py