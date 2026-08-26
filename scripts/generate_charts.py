import os

import matplotlib.pyplot as plt


def create_charts(output_dir):
    os.makedirs(output_dir, exist_ok=True)

    # Chart 1: Global Disease Burden by Age (Mock/Representative Data based on epidemiology)
    labels = ["< 5 Years", "5 - 64 Years", "> 65 Years"]
    cases = [205, 410, 70]  # in millions (Total ~685M)
    deaths = [50, 40, 110]  # in thousands (Total ~200K)

    fig, ax1 = plt.subplots(figsize=(8, 5))
    color = "tab:blue"
    ax1.set_xlabel("Age Group")
    ax1.set_ylabel("Infections (Millions)", color=color)
    ax1.bar(labels, cases, color=color, alpha=0.6, label="Infections")
    ax1.tick_params(axis="y", labelcolor=color)

    ax2 = ax1.twinx()
    color = "tab:red"
    ax2.set_ylabel("Deaths (Thousands)", color=color)
    ax2.plot(labels, deaths, color=color, marker="o", linewidth=2, label="Deaths")
    ax2.tick_params(axis="y", labelcolor=color)

    plt.title("Global Norovirus Disease Burden by Age Group")
    fig.tight_layout()
    plt.savefig(os.path.join(output_dir, "burden_by_age.png"), dpi=300)
    plt.close()

    # Chart 2: Outbreak Settings in China
    settings = [
        "Primary/Secondary\nSchools & Colleges",
        "Kindergartens\n& Nurseries",
        "Restaurants\n& Public Places",
        "Hospitals\n& Workplaces",
    ]
    percentages = [70.2, 21.0, 5.0, 3.8]

    plt.figure(figsize=(8, 5))
    plt.pie(
        percentages,
        labels=settings,
        autopct="%1.1f%%",
        startangle=140,
        colors=["#ff9999", "#66b3ff", "#99ff99", "#ffcc99"],
    )
    plt.title("Norovirus Outbreak Settings in China")
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "outbreak_settings.png"), dpi=300)
    plt.close()

    # Chart 3: Seasonality (Representative data)
    months = [
        "Jan",
        "Feb",
        "Mar",
        "Apr",
        "May",
        "Jun",
        "Jul",
        "Aug",
        "Sep",
        "Oct",
        "Nov",
        "Dec",
    ]
    # Example incidence curve peaking in winter
    incidence = [85, 70, 50, 30, 15, 10, 5, 8, 20, 45, 75, 90]

    plt.figure(figsize=(10, 4))
    plt.plot(months, incidence, marker="s", color="#8B0000", linewidth=2)
    plt.fill_between(months, incidence, color="#8B0000", alpha=0.2)
    plt.title("Typical Seasonal Distribution of Norovirus Outbreaks")
    plt.xlabel("Month")
    plt.ylabel("Relative Outbreak Frequency (%)")
    plt.grid(True, linestyle="--", alpha=0.6)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "seasonality.png"), dpi=300)
    plt.close()


if __name__ == "__main__":
    create_charts("review_materials")
