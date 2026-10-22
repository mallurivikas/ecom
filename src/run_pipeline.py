import subprocess
import sys


STEPS = [
    ["-m", "src.ingestion.extract_postgres"],
    ["-m", "src.transformation.transform_silver"],
    ["-m", "src.transformation.transform_gold"],
    ["-m", "src.warehouse.load_warehouse"],
]


def run_step(command):
    print(f"\nRunning: python {' '.join(command)}")

    result = subprocess.run(
        [sys.executable, *command]
    )

    if result.returncode != 0:
        print(f"Pipeline stopped: python {' '.join(command)}")
        sys.exit(result.returncode)


def main():
    print("STARTING ECOM PIPELINE")

    for command in STEPS:
        run_step(command)

    print("\nECOM PIPELINE COMPLETED")


if __name__ == "__main__":
    main()