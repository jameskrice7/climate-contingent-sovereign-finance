PYTHON ?= python3
TECTONIC ?= tectonic
LAKE ?= lake

.PHONY: reproduce numerics check paper response lean qa
reproduce:
	$(MAKE) numerics
	$(MAKE) check
	$(MAKE) paper
	$(MAKE) response
	$(MAKE) lean
numerics:
	$(PYTHON) -m replication.run
check:
	$(PYTHON) -m unittest discover -s tests -v
	$(PYTHON) -m replication.check_outputs
paper:
	$(PYTHON) -m replication.export_submission
	cd paper && $(TECTONIC) -X compile main.tex --outdir . --keep-logs
response:
	cd reviews && $(TECTONIC) -X compile response_round2.tex --outdir . --keep-logs
lean:
	cd lean_verification && $(LAKE) build
qa:
	$(PYTHON) -m replication.render_pdfs
	$(PYTHON) -m replication.compare_length
