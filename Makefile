PYTHON ?= python3
TECTONIC ?= tectonic
LAKE ?= lake

.PHONY: reproduce numerics check paper lean qa
reproduce:
	$(MAKE) numerics
	$(MAKE) check
	$(MAKE) paper
	$(MAKE) lean
numerics:
	$(PYTHON) -m replication.run
check:
	$(PYTHON) -m unittest discover -s tests -v
	$(PYTHON) -m replication.check_outputs
paper:
	cd paper && $(TECTONIC) -X compile main.tex --outdir . --keep-logs
lean:
	cd lean_verification && $(LAKE) build
qa:
	$(PYTHON) -m replication.render_pdfs
