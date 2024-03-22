install-requirements:
	pip install -r requirements.txt

create-requirements:
	pip list > requirements.txt --format freeze