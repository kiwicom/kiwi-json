reqs:
	pip-compile --upgrade --output-file ./requirements.txt ./requirements.in
	pip-compile --upgrade --output-file ./test-requirements.txt ./test-requirements.in

.PHONY: reqs
