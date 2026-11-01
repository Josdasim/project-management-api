REPORTS_DIR := reports

.PHONY: lint format check check-format check-quality run-dev clean

# Revisar codigo y corregir automaticamente
lint:
	ruff check --fix

# Aplicar formato
format:
	ruff format .

# Verificar codigo sin corregir
check:
	@mkdir -p $(REPORTS_DIR)
	@echo "Ejecutando Ruff para revision de lint..."
	@ruff check . > $(REPORTS_DIR)/lint-report.txt 2>&1; \
	if [ $$? -eq 0 ]; then \
		echo "Ruff Lint: No encontro problemas"; \
	else \
		echo "Ruff Lint: Encontro problemas. Revisa en '$(REPORTS_DIR)/lint-report.txt'"; \
		exit 1; \
	fi

# Verifica formato sin corregir
check-format:
	@mkdir -p $(REPORTS_DIR)
	@echo "Ejecutando Ruff para revision de formato..."
	@ruff format --check . > $(REPORTS_DIR)/format-report.txt 2>&1; \
	if [ $$? -eq 0 ]; then \
		echo "Ruff Format: No encontro problemas"; \
	else \
		echo "Ruff Format: Encontro problemas. Revisa en '$(REPORTS_DIR)/format-report.txt'"; \
		exit 1; \
	fi

# Correr revisiones de lint y formato
check-quality: check-format check

# Correr servidor de desarrollo de FastAPI
run-dev: 
	uvicorn src.main:app --reload

# Limpiar archivos temporales, caches y reportes
clean:
	rm -rf $(REPORTS_DIR)
	find . -type f -name '*.pyc' -delete
	find . -type f -name '__pycache__' -delete
	rm -rf .ruff_cache
	rm -rf .pytest_cache