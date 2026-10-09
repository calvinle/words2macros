# Used by `sam build` (BuildMethod: makefile). SAM sets ARTIFACTS_DIR.
# Installs locked runtime dependencies as Linux arm64 wheels, then copies our package.
# boto3 is not installed: the Lambda Python runtime already includes it.

build-AnalyzeFunction:
	uv export --frozen --no-dev --no-editable --no-emit-project -o $(ARTIFACTS_DIR)/requirements.txt
	uv pip install --no-installer-metadata --no-compile-bytecode \
		--python-platform aarch64-manylinux2014 --python 3.13 \
		--target $(ARTIFACTS_DIR) -r $(ARTIFACTS_DIR)/requirements.txt
	rm $(ARTIFACTS_DIR)/requirements.txt
	$(MAKE) copy-package

# The kill switch only needs boto3 (built in), so no dependencies are installed.
build-KillSwitchFunction: copy-package

copy-package:
	cp -r src/words2macros $(ARTIFACTS_DIR)/
	find $(ARTIFACTS_DIR) -name __pycache__ -type d -prune -exec rm -rf {} +
