import argparse
from .perturbation.perturbation import perturbation


def main():
    
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--lang", 
        type=str, 
        required=True,
        help="The language of the code snippet."
        )
    parser.add_argument(
        "--file", 
        type=str,
        required=True,
        help="The file containing the original code, it should be a jsonl file."
        )
    parser.add_argument(
        "--mi", 
        type=int, 
        default=15,
        help="The maximum number of iterations."
        )
    parser.add_argument(
        "--st", 
        type=int, 
        default=0.2,
        help="The similarity score threshold."
        )
    parser.add_argument(
        "--temper",
        type=float,
        default=2,
        help="The temperature for boltzmann selection."
        )

    args = parser.parse_args()
    lang = args.lang
    code_file = args.file
    max_iter = args.mi
    similarity_threshold = args.st
    temperature = args.temper

    perturbation(lang, code_file, max_iter, similarity_threshold, temperature)


if __name__ == "__main__":
    main()