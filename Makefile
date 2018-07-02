reqs:
	pip-compile --upgrade --output-file ./requirements.txt ./requirements.in
	pip-compile --upgrade --output-file ./test-requirements.txt ./test-requirements.in

test:
	pytest ./test

dist:
	python setup.py sdist

pypi:
	twine upload ./dist/kiwi-json-*.tar.gz --repository=kiwi

.PHONY: reqs test dist pypi
