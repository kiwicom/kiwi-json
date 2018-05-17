reqs:
	pip-compile --upgrade --output-file ./requirements.txt ./requirements.in
	pip-compile --upgrade --output-file ./test-requirements.txt ./test-requirements.in

test:
	pytest ./test

dist:
	python setup.py sdist

.PHONY: reqs test dist
