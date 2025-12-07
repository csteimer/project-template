SPHINXBUILD   ?= sphinx-build
SOURCEDIR     = .
BUILDDIR      = build

.PHONY: help html clean

help:
	@echo "make html  - build HTML documentation"
	@echo "make clean - remove build artifacts"

html:
	$(SPHINXBUILD) -b html $(SOURCEDIR) $(BUILDDIR)/html

clean:
	rm -rf $(BUILDDIR)
