.PHONY:	all
all:

.PHONY:	bundle
bundle:
	npx rollup -c

.PHONY:	check
check: bundle
	luacheck slipbox/filters/*.lua --globals describe it assert pandoc
	cd slipbox; cat filters/*.test.lua | lua
	npx eslint test --global describe --global it --global beforeEach --rule 'no-unused-vars: 0'
	npm run lint
	npm test
	pylint slipbox --fail-under=10 -d R0903
	cd slipbox; pytest --cov=. --cov-fail-under=80 --cov-report=term-missing --cov-branch
	@echo "Yay!"

.PHONY:	docs
docs:	bundle
	python -m slipbox docs/docs.db docs/tutorial.md \
		-c ' --bibliography docs/tutorial.bib' \
		-d ' -o docs/index.html -c basic.css'

.PHONY:	dist
dist:	bundle check
	python setup.py sdist bdist_wheel
	twine upload dist/*
