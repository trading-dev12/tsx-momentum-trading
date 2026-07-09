"""
Slippage Validator
"""

from research.out_of_sample_validator import run_out_of_sample_validation


def run_slippage_validation():
    

    slippage_tests = [0.0, 0.0005, 0.001, 0.002]

    for slippage in slippage_tests:
        print("\n" + "=" * 70)
        print(f"SLIPPAGE TEST: {slippage * 100:.2f}%")
        print("=" * 70)

        run_out_of_sample_validation(
            split_year=2024,
            min_tmqs=100,
            min_rvol=1.5,
            breakout_only=True,
            slippage_percent=slippage,
        )