.PHONY: verify data eval test app

data:
	python src/demo_data.py

eval:
	python scripts/run_evaluation.py

test:
	pytest -q

verify: data eval test
	@echo "PolicyGuard v2 verification complete."

app:
	streamlit run app.py
