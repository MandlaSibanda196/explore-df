.PHONY: clean build publish bump-patch bump-minor bump-major deploy

# Version bumping
bump-patch:
	@current_version=$$(grep -E "version\s*=\s*['\"].*['\"]" pyproject.toml | grep -oE "[0-9]+\.[0-9]+\.[0-9]+"); \
	IFS=. read -r major minor patch <<< "$$current_version"; \
	new_patch=$$((patch + 1)); \
	new_version="$$major.$$minor.$$new_patch"; \
	sed -i.bak "s/version = \"$$current_version\"/version = \"$$new_version\"/" pyproject.toml; \
	sed -i.bak "s/version=\"$$current_version\"/version=\"$$new_version\"/" setup.py; \
	rm -f pyproject.toml.bak setup.py.bak; \
	echo "Version bumped to $$new_version"

clean:
	rm -rf dist/ build/ *.egg-info

build: clean
	python -m build

publish: build
	twine upload dist/*

# Development commands
install: clean
	pip install -e .

test:
	pytest

# All in one command
deploy: bump-patch clean build publish 