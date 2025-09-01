preflight:
	python3 scripts/validate_fcp_schema.py
	python3 scripts/qsecure_preflight.py --strict-rotation

weekly:
	python3 scripts/quantum/qsim_belief_evolution.py --config "Codex/System/Quantum_CHRS.yaml::simulations.superpositional_belief" > reports/.q_belief.json
	python3 scripts/quantum/qsim_entangled_sps.py --config "Codex/System/Quantum_CHRS.yaml::simulations.entangled_multi_sp" > reports/.q_entangle.json
	python3 scripts/quantum/qsim_decoherence_filtering.py --config "Codex/System/Quantum_CHRS.yaml::simulations.decoherence_filtering" > reports/.q_decoherence.json
	python3 scripts/quantum/gen_quantum_chrs_status.py --belief reports/.q_belief.json --entangle reports/.q_entangle.json --decoherence reports/.q_decoherence.json --out-md reports/Quantum_CHRS_Status.md --out-json reports/Quantum_CHRS_Status.json
	python3 scripts/chorus/merge_shepherd_reflections.py
	python3 scripts/lint/audit_chain_verify.py

audit:
	python3 scripts/fcp_check.py --fcp Codex/System/FCP.yaml --audit Codex/Core/FCP_Audit.yaml
	python3 scripts/fcp_audit_translate.py --audit Codex/Core/FCP_Audit.yaml --fcp Codex/System/FCP.yaml

resonance:
	python3 scripts/inject_sp_fcp_fields.py
	python3 scripts/chorus/merge_shepherd_reflections.py
	python3 scripts/quantum/qsim_belief_evolution.py --config "Codex/System/Quantum_CHRS.yaml::simulations.superpositional_belief" > reports/.q_belief.json
	python3 scripts/quantum/qsim_entangled_sps.py --config "Codex/System/Quantum_CHRS.yaml::simulations.entangled_multi_sp" > reports/.q_entangle.json
	python3 scripts/quantum/qsim_decoherence_filtering.py --config "Codex/System/Quantum_CHRS.yaml::simulations.decoherence_filtering" > reports/.q_decoherence.json
	python3 scripts/quantum/gen_quantum_chrs_status.py --belief reports/.q_belief.json --entangle reports/.q_entangle.json --decoherence reports/.q_decoherence.json --out-md reports/Quantum_CHRS_Status.md --out-json reports/Quantum_CHRS_Status.json

.PHONY: preflight weekly audit resonance

codex-check:
	python3 scripts/validate_codex_layout.py

codex-check-json:
	python3 scripts/validate_codex_layout.py --json > reports/Codex_Layout_Check.json

codex-scaffold:
	python3 scripts/validate_codex_layout.py --create-stubs
	python3 scripts/populate_theory_stubs.py

.PHONY: codex-check codex-check-json codex-scaffold

yaml-fix:
	python3 scripts/fix_yaml_docstart.py

yaml-lint:
	yamllint -s Codex


.PHONY: yaml-fix yaml-lint
