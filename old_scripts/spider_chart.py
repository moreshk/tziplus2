import matplotlib.pyplot as plt
import numpy as np

def get_user_input():
    parameters = [
        "Risk", "Yield", "Capital Gain", "Maturity Period",
        "Yield Frequency", "Liquidity", "Access"
    ]
    values = {}
    for param in parameters:
        while True:
            try:
                value = float(input(f"Enter value for {param} (0-10): "))
                if 0 <= value <= 10:
                    values[param] = value
                    break
                else:
                    print("Please enter a value between 0 and 10.")
            except ValueError:
                print("Please enter a valid number.")
    return values

def create_spider_chart(data):
    categories = list(data.keys())
    values = list(data.values())

    # Number of variables
    N = len(categories)

    # What will be the angle of each axis in the plot? (we divide the plot / number of variable)
    angles = [n / float(N) * 2 * np.pi for n in range(N)]
    values += values[:1]
    angles += angles[:1]

    # Initialize the spider plot
    fig, ax = plt.subplots(figsize=(6, 6), subplot_kw=dict(projection='polar'))

    # Draw one axis per variable + add labels
    plt.xticks(angles[:-1], categories)

    # Draw ylabels
    ax.set_rlim(0, 10)
    ax.set_rticks(np.arange(1, 11, 2))

    # Plot data
    ax.plot(angles, values)
    ax.fill(angles, values, 'b', alpha=0.1)

    # Add a title
    plt.title("Investment Parameters Spider Chart")

    # Show the graph
    plt.tight_layout()
    plt.show()

def main():
    print("Welcome to the Investment Spider Chart Generator!")
    data = get_user_input()
    create_spider_chart(data)

if __name__ == "__main__":
    main()