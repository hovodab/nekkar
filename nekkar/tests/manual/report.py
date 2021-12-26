import matplotlib.pyplot as plt


COLORS = [
    'black',
    'red',
    'green',
    'yellow',
    'blue',
    'cyan',
    'crimson',
    'pink',
    'orange',
    'violet',
]


def get_lines(logs):
    lines = list()
    first_elements = list()
    for log in logs:
        with open(log, "r") as f:
            data = f.read()
        line = data.split()
        lines.append(line)
        first_elements.append(float(line[0]))

    minimum = min(first_elements)
    result = list()
    for line in lines:
        x = [float(value) - minimum for value in line]
        result.append(x)

    total_count = sum([len(line) for line in lines])
    whole = set()
    for line in lines:
        whole.update(line)

    print("TOTAL COUNT: ", total_count)
    print("TOTAL UNIQUE COUNT: ", len(whole))
    return result


def get_rate(line):
    dt = 0
    for i in range(len(line) - 1):
        dt += line[i + 1] - line[i]
    the_rate = dt / (len(line) - 1)
    min_rate = 60000 / the_rate
    return the_rate, min_rate


def print_rates(lines):
    for index, line in enumerate(lines):
        the_rate, min_rate = get_rate(line)
        print(f"Rate for {index}: {the_rate} --- {min_rate}")

    total = list()
    for line in lines:
        total += line
    total = sorted(total)
    total_diff = total[-1] - total[0]
    total_rate = total_diff / len(total)
    the_rate, min_rate = get_rate(total)
    print(f"Rate for ALL: {the_rate} --- {min_rate}")
    print(f"TOTAL RATE: 1 hit takes {total_rate} ms +++ In one minute: {60000 / total_rate}")


def main(number_of_sources):
    logs = [f"executable{i}.log" for i in range(1, 1 + number_of_sources)]
    lines = get_lines(logs)
    print_rates(lines)
    plt.figure(figsize=(15, 5))
    for index, line in enumerate(lines):
        x = line
        y = [index] * len(x)
        plt.plot(x, y, 'o', color=COLORS[index])

    plt.ylim(-20, 20)
    plt.show()


if __name__ == "__main__":
    main(2)
