"""Offline sample or normalized JSON valuation from the command line."""

import argparse
import json
from pathlib import Path
from dcf_code import DCFModel, DCFAssumptions
from dcf_loader import demo_document, parse_document


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--financials", type=Path, help="dcf-financials-v1 JSON file; default is synthetic demo"
    )
    parser.add_argument("--wacc", type=float, default=0.065, help="Decimal WACC, e.g. 0.065")
    parser.add_argument(
        "--growth",
        type=float,
        nargs=5,
        default=[0.05] * 5,
        help="Five decimal revenue growth rates",
    )
    parser.add_argument("--terminal-growth", type=float, default=0.02)
    args = parser.parse_args()
    try:
        doc = json.loads(args.financials.read_text()) if args.financials else demo_document()
        result = DCFModel(
            parse_document(doc),
            DCFAssumptions(args.growth, args.terminal_growth, wacc_override=args.wacc),
        ).calculate()
        print(json.dumps(result, indent=2, allow_nan=False))
    except (ValueError, OSError) as e:
        parser.error(str(e))


if __name__ == "__main__":
    main()
