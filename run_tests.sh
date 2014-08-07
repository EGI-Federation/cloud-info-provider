virtualenv VENV
source VENV/bin/activate
pip install -r requirements.txt
pip install -r test-requirements.txt

echo "Running unit tests with coverage"

nosetests  --with-cover --cover-package=cloud_bdii --cover-inclusive --cover-html

echo
echo "********************************************************************************"
echo "Running PEP8" tests
flake8 cloud_bdii/

deactivate
