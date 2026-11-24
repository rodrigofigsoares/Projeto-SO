# Atalhos reproduzíveis executados a partir da raiz do repositório.

SHELL := /bin/bash

RUN_ID := $(shell date +%Y-%m-%d_%H-%M-%S)
RESULT_DIR ?= analysis/runs/$(RUN_ID)
RESULT_ABS := $(abspath $(RESULT_DIR))

NATIVE_RESULT_DIR ?= analysis/runs/$(RUN_ID)_native-linux
DOCKER_RESULT_DIR ?= analysis/runs/$(RUN_ID)_docker-linux
COMPARISON_DIR ?= analysis/runs/$(RUN_ID)_comparison

RUNS := 10
POLL_INTERVAL_MS := 50
NATIVE_BENCH_DIR ?= /tmp

# Digests fixos: a mesma imagem será usada mesmo que a tag mude no registry.
GCC_IMAGE := gcc@sha256:5e927c284bf55a7dc796262e311a0703344f62f41f5621eb56843111b1d37e15
PYTHON_IMAGE := python@sha256:efd0600c261faa9939c6b248af12908f96ac5f15463657a92302b058064a1aba
INOTIFY_SIMPLE_VERSION := 1.3.5

export RESULT_DIR RUNS POLL_INTERVAL_MS NATIVE_BENCH_DIR

.PHONY: help run_local run_docker_macos run_native_linux run_docker_linux run_linux_comparison
.PHONY: check_macos check_linux check_docker check_native_tools
.PHONY: prepare_docker benchmarks_docker monitors_docker
.PHONY: prepare_native benchmarks_native monitors_native
.PHONY: summaries metadata_docker metadata_native show_results
.NOTPARALLEL:

help:
	@echo "Uso no macOS (exploratório):"
	@echo "  make run_docker_macos"
	@echo ""
	@echo "Uso na mesma máquina Linux (comparação válida):"
	@echo "  make run_native_linux"
	@echo "  make run_docker_linux"
	@echo "  make run_linux_comparison   # executa os dois e compara as médias"
	@echo ""
	@echo "As saídas ficam em analysis/runs/."

# Compatibilidade com o nome usado inicialmente. O aviso evita chamar a coleta
# de nativa: no Mac ela sempre passa pela VM Linux do Docker Desktop.
run_local:
	@echo "AVISO: run_local foi renomeado para run_docker_macos." >&2
	@$(MAKE) --no-print-directory run_docker_macos RESULT_DIR="$(RESULT_DIR)"

run_docker_macos: check_macos check_docker
	@echo "AVISO: Docker Desktop usa uma VM Linux; esta coleta não é macOS nativo."
	@$(MAKE) --no-print-directory prepare_docker
	@$(MAKE) --no-print-directory benchmarks_docker BENCH_ENV=docker-desktop-linux
	@$(MAKE) --no-print-directory monitors_docker
	@$(MAKE) --no-print-directory summaries
	@$(MAKE) --no-print-directory metadata_docker BENCH_ENV=docker-desktop-linux EXECUTION=docker-desktop-macos
	@$(MAKE) --no-print-directory show_results

run_native_linux: check_linux check_native_tools
	@echo "Executando diretamente no host Linux, sem container..."
	@$(MAKE) --no-print-directory prepare_native
	@$(MAKE) --no-print-directory benchmarks_native BENCH_ENV=native-linux
	@$(MAKE) --no-print-directory monitors_native
	@$(MAKE) --no-print-directory summaries
	@$(MAKE) --no-print-directory metadata_native BENCH_ENV=native-linux
	@$(MAKE) --no-print-directory show_results

run_docker_linux: check_linux check_docker
	@echo "Executando em container no mesmo host Linux..."
	@$(MAKE) --no-print-directory prepare_docker
	@$(MAKE) --no-print-directory benchmarks_docker BENCH_ENV=docker-linux
	@$(MAKE) --no-print-directory monitors_docker
	@$(MAKE) --no-print-directory summaries
	@$(MAKE) --no-print-directory metadata_docker BENCH_ENV=docker-linux EXECUTION=docker-linux
	@$(MAKE) --no-print-directory show_results

run_linux_comparison: check_linux check_native_tools check_docker
	@echo "1/3 — coleta Linux nativo"
	@$(MAKE) --no-print-directory run_native_linux RESULT_DIR="$(NATIVE_RESULT_DIR)"
	@echo "2/3 — coleta Docker no mesmo Linux"
	@$(MAKE) --no-print-directory run_docker_linux RESULT_DIR="$(DOCKER_RESULT_DIR)"
	@echo "3/3 — comparação das médias"
	@mkdir -p "$(abspath $(COMPARISON_DIR))"
	@python3 analysis/compare_benchmarks.py \
		"$(abspath $(NATIVE_RESULT_DIR))/benchmarks_summary.csv" \
		"$(abspath $(DOCKER_RESULT_DIR))/benchmarks_summary.csv" \
		"$(abspath $(COMPARISON_DIR))/benchmarks_comparison.csv"
	@{ \
		echo "native_dir=$(NATIVE_RESULT_DIR)"; \
		echo "docker_dir=$(DOCKER_RESULT_DIR)"; \
		echo "comparison_created_at=$$(date '+%Y-%m-%dT%H:%M:%S%z')"; \
	} > "$(abspath $(COMPARISON_DIR))/metadata.txt"
	@echo ""
	@echo "Comparação concluída em: $(COMPARISON_DIR)"
	@cat "$(abspath $(COMPARISON_DIR))/benchmarks_comparison.csv"

check_macos:
	@os=$$(uname -s); test "$$os" = "Darwin" || { \
		echo "ERRO: este alvo exige macOS; sistema encontrado: $$os" >&2; exit 1; \
	}

check_linux:
	@os=$$(uname -s); test "$$os" = "Linux" || { \
		echo "ERRO: este alvo exige Linux nativo; sistema encontrado: $$os" >&2; \
		echo "No Mac, use apenas: make run_docker_macos" >&2; exit 1; \
	}

check_docker:
	@command -v docker >/dev/null || { echo "ERRO: Docker não encontrado." >&2; exit 1; }
	@command -v python3 >/dev/null || { echo "ERRO: python3 não encontrado." >&2; exit 1; }
	@docker info >/dev/null 2>&1 || { \
		echo "ERRO: o daemon Docker não está em execução ou não está acessível." >&2; exit 1; \
	}

check_native_tools:
	@command -v gcc >/dev/null || { echo "ERRO: gcc não encontrado." >&2; exit 1; }
	@command -v make >/dev/null || { echo "ERRO: make não encontrado." >&2; exit 1; }
	@command -v python3 >/dev/null || { echo "ERRO: python3 não encontrado." >&2; exit 1; }
	@python3 -m venv --help >/dev/null 2>&1 || { \
		echo "ERRO: módulo venv ausente. No Ubuntu/Debian, instale python3-venv." >&2; exit 1; \
	}

prepare_docker:
	@mkdir -p "$(RESULT_ABS)"
	@docker image inspect "$(GCC_IMAGE)" >/dev/null 2>&1 || docker pull "$(GCC_IMAGE)"
	@docker image inspect "$(PYTHON_IMAGE)" >/dev/null 2>&1 || docker pull "$(PYTHON_IMAGE)"

benchmarks_docker:
	@echo "Executando microbenchmarks no Docker (aquecimento + $(RUNS) rodadas válidas)..."
	@docker run --rm \
		-v "$(CURDIR)/bench_c:/src:ro" \
		-v "$(RESULT_ABS):/out" \
		"$(GCC_IMAGE)" bash -lc 'set -eu; \
		cp -r /src /work; cd /work; make clean all >/dev/null; \
		{ \
		  ./bench_syscall --env "$(BENCH_ENV)" --runs "$(RUNS)" --n 1000000; \
		  ./bench_fork --env "$(BENCH_ENV)" --runs "$(RUNS)" --n 2000 | tail -n +2; \
		  ./bench_pipe --env "$(BENCH_ENV)" --runs "$(RUNS)" --n 100000 | tail -n +2; \
		  ./bench_disk --env "$(BENCH_ENV)" --runs "$(RUNS)" --n 64 --dir /tmp | tail -n +2; \
		  ./bench_alloc --env "$(BENCH_ENV)" --runs "$(RUNS)" --n 200000 | tail -n +2; \
		} > /out/benchmarks_raw.csv'

monitors_docker:
	@echo "Executando polling x inotify no Docker..."
	@docker run --rm \
		-v "$(CURDIR)/henri_checkpoint_1:/src:ro" \
		-v "$(RESULT_ABS):/out" \
		"$(PYTHON_IMAGE)" bash -lc 'set -eu; \
		PIP_ROOT_USER_ACTION=ignore pip install --disable-pip-version-check --quiet "inotify-simple==$(INOTIFY_SIMPLE_VERSION)"; \
		cp -r /src /work; cd /work; \
		bash demo.sh /tmp/projeto-so-monitor-demo "$(POLL_INTERVAL_MS)"; \
		cp /tmp/poll.csv /out/poll.csv; \
		cp /tmp/ino.csv /out/inotify.csv'

prepare_native:
	@mkdir -p "$(RESULT_ABS)/build"
	@cp -R bench_c "$(RESULT_ABS)/build/"
	@$(MAKE) --no-print-directory -C "$(RESULT_ABS)/build/bench_c" clean all
	@python3 -m venv "$(RESULT_ABS)/venv"
	@"$(RESULT_ABS)/venv/bin/pip" install --disable-pip-version-check --quiet \
		"inotify-simple==$(INOTIFY_SIMPLE_VERSION)"

benchmarks_native:
	@echo "Executando microbenchmarks no host (aquecimento + $(RUNS) rodadas válidas)..."
	@cd "$(RESULT_ABS)/build/bench_c"; { \
		./bench_syscall --env "$(BENCH_ENV)" --runs "$(RUNS)" --n 1000000; \
		./bench_fork --env "$(BENCH_ENV)" --runs "$(RUNS)" --n 2000 | tail -n +2; \
		./bench_pipe --env "$(BENCH_ENV)" --runs "$(RUNS)" --n 100000 | tail -n +2; \
		./bench_disk --env "$(BENCH_ENV)" --runs "$(RUNS)" --n 64 --dir "$(NATIVE_BENCH_DIR)" | tail -n +2; \
		./bench_alloc --env "$(BENCH_ENV)" --runs "$(RUNS)" --n 200000 | tail -n +2; \
	} > "$(RESULT_ABS)/benchmarks_raw.csv"

monitors_native:
	@echo "Executando polling x inotify diretamente no host Linux..."
	@demo_dir="/tmp/projeto-so-monitor-demo-$$$$"; \
		. "$(RESULT_ABS)/venv/bin/activate"; \
		cd henri_checkpoint_1; \
		bash demo.sh "$$demo_dir" "$(POLL_INTERVAL_MS)"; \
		cp /tmp/poll.csv "$(RESULT_ABS)/poll.csv"; \
		cp /tmp/ino.csv "$(RESULT_ABS)/inotify.csv"; \
		rmdir "$$demo_dir"

summaries:
	@python3 analysis/summarize_benchmarks.py \
		"$(RESULT_ABS)/benchmarks_raw.csv" \
		"$(RESULT_ABS)/benchmarks_summary.csv"
	@python3 analysis/summarize_monitor_demo.py \
		"$(RESULT_ABS)/poll.csv" \
		"$(RESULT_ABS)/inotify.csv" \
		> "$(RESULT_ABS)/monitor_summary.csv"

metadata_native:
	@{ \
		echo "collected_at=$$(date '+%Y-%m-%dT%H:%M:%S%z')"; \
		echo "git_commit=$$(git rev-parse HEAD)"; \
		echo "execution=native-linux"; \
		echo "host_kernel=$$(uname -sr)"; \
		echo "host_arch=$$(uname -m)"; \
		echo "gcc=$$(gcc -dumpfullversion -dumpversion)"; \
		echo "python=$$(python3 --version 2>&1)"; \
		echo "benchmark_env=$(BENCH_ENV)"; \
		echo "benchmark_dir=$(NATIVE_BENCH_DIR)"; \
		echo "valid_runs=$(RUNS)"; \
		echo "poll_interval_ms=$(POLL_INTERVAL_MS)"; \
	} > "$(RESULT_ABS)/metadata.txt"

metadata_docker:
	@{ \
		echo "collected_at=$$(date '+%Y-%m-%dT%H:%M:%S%z')"; \
		echo "git_commit=$$(git rev-parse HEAD)"; \
		echo "execution=$(EXECUTION)"; \
		echo "host_kernel=$$(uname -sr)"; \
		echo "host_arch=$$(uname -m)"; \
		echo "docker_engine=$$(docker version --format '{{.Server.Version}}')"; \
		echo "benchmark_env=$(BENCH_ENV)"; \
		echo "valid_runs=$(RUNS)"; \
		echo "poll_interval_ms=$(POLL_INTERVAL_MS)"; \
		echo "gcc_image=$(GCC_IMAGE)"; \
		echo "python_image=$(PYTHON_IMAGE)"; \
	} > "$(RESULT_ABS)/metadata.txt"

show_results:
	@echo ""
	@echo "Coleta concluída em: $(RESULT_DIR)"
	@echo ""
	@cat "$(RESULT_ABS)/benchmarks_summary.csv"
	@echo ""
	@cat "$(RESULT_ABS)/monitor_summary.csv"
