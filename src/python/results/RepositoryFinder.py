import csv
import math
import random


# Function to convert CSV to java_repos.txt
def convert_csv_to_repos(input_file, output_file):
    with open(input_file, "r") as csvfile:
        reader = csv.DictReader(csvfile)
        with open(output_file, "w") as file:
            for row in reader:
                file.write(f"{row['name']}\n")


def sample_repos(input_file, output_file, sample_size=500):
    with open(input_file, "r") as file:
        repos = file.readlines()

    repos = [repo.strip() for repo in repos]

    if len(repos) < sample_size:
        raise ValueError(f"Not enough repos to sample {sample_size} unique entries.")

    sampled_repos = random.sample(repos, sample_size)

    with open(output_file, "x") as file:
        for repo in sampled_repos:
            file.write(f"{repo}\n")


if __name__ == "__main__":
    number_of_repos = {"python": 55862, "java": 17882}
    input_file = "../data/rq1_java_repos.txt"
    output_file = "../data/rq3_repos.txt"
    sample_size = math.ceil(number_of_repos["java"] / 20)

    sample_repos(input_file, output_file, sample_size)
    print(f"Sampled {sample_size} unique repositories written to {output_file}")
