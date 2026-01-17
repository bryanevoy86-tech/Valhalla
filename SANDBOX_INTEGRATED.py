from sandbox_integrated.orchestrator import run_integrated

if __name__ == "__main__":
    # max_cycles=None runs forever
    run_integrated(
        config_path="configs/sandbox_integrated.json",
        out_dir="reports/integrated_sandbox",
        max_cycles=None
    )
