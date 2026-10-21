import random
from datetime import date, timedelta
from pathlib import Path

import pandas as pd


def generate_trade_data(
    number_of_trades: int = 2000,
    seed: int = 42,
    include_anomalies: bool = False,
) -> pd.DataFrame:
    """
    Generate synthetic bond-trade records.

    If include_anomalies=False:
        Generate normal training examples using common relationships.

    If include_anomalies=True:
        Include deliberately unusual trades for testing.
    """

    rng = random.Random(seed)
    today = date.today()

    # Possible counterparties and portfolios.
    counterparties = [f"CP{i:03d}" for i in range(1, 21)]
    portfolios = [f"PF{i:03d}" for i in range(1, 11)]

    # Common counterparty–portfolio relationships.
    common_relationships = [
        ("CP001", "PF001"),
        ("CP001", "PF002"),
        ("CP002", "PF001"),
        ("CP002", "PF002"),
        ("CP003", "PF003"),
        ("CP004", "PF004"),
        ("CP005", "PF005"),
        ("CP006", "PF006"),
        ("CP007", "PF007"),
        ("CP008", "PF008"),
        ("CP009", "PF009"),
        ("CP010", "PF010"),
    ]

    records = []

    # Inject approximately 3% unusual examples into the test dataset.
    anomaly_count = (
        max(1, int(number_of_trades * 0.03))
        if include_anomalies
        else 0
    )

    for i in range(number_of_trades):

        # The first few records are deliberately unusual when testing.
        is_test_anomaly = i < anomaly_count

        if is_test_anomaly:
            # A rare counterparty–portfolio combination.
            counterparty_id = "CP020"
            portfolio_id = "PF010"
        else:
            # Normal examples use known common relationships.
            counterparty_id, portfolio_id = rng.choice(
                common_relationships
            )

        # Generate a creation date within the past year.
        created_date = today - timedelta(
            days=rng.randint(0, 365)
        )

        # Generate a maturity date between 30 days and 10 years ahead.
        maturity_date = today + timedelta(
            days=rng.randint(30, 3650)
        )

        # Give deliberately unusual test records an extreme maturity.
        if is_test_anomaly:
            maturity_date = today + timedelta(days=365 * 80)

        # Generate a trade version.
        version = rng.choices(
            [1, 2, 3],
            weights=[0.75, 0.20, 0.05],
        )[0]

        # Store one trade as a dictionary.
        records.append(
            {
                "trade_id": f"TR{i + 1:06d}",
                "version": version,
                "counterparty_id": counterparty_id,
                "portfolio_id": portfolio_id,
                "maturity_date": maturity_date.strftime("%d/%m/%Y"),
                "created_date": created_date.strftime("%d/%m/%Y"),
                "expired": "N",
            }
        )

    # Convert the list of trade dictionaries into a DataFrame.
    df = pd.DataFrame(records)

    # Shuffle the records so unusual examples aren't all at the top.
    df = df.sample(
        frac=1,
        random_state=seed,
    ).reset_index(drop=True)

    return df


if __name__ == "__main__":

    # Find the project root regardless of the terminal's current folder.
    project_root = Path(__file__).resolve().parent.parent

    # Create the ml directory if it doesn't already exist.
    output_dir = project_root / "ml"
    output_dir.mkdir(parents=True, exist_ok=True)

    # -------------------------------------------------
    # 1. Generate the training dataset
    # -------------------------------------------------

    # These examples use common relationships and do not
    # contain deliberately injected anomalies.
    train_df = generate_trade_data(
        number_of_trades=2000,
        seed=42,
        include_anomalies=False,
    )

    train_path = output_dir / "synthetic_trades_train.csv"
    train_df.to_csv(train_path, index=False)

    # -------------------------------------------------
    # 2. Generate the test dataset
    # -------------------------------------------------

    # These examples include deliberately unusual relationships
    # and extremely long maturities for prototype testing.
    test_df = generate_trade_data(
        number_of_trades=500,
        seed=123,
        include_anomalies=True,
    )

    test_path = output_dir / "synthetic_trades_test.csv"
    test_df.to_csv(test_path, index=False)

    # -------------------------------------------------
    # 3. Display the results
    # -------------------------------------------------

    print("Synthetic trade datasets generated successfully.")

    print(f"\nTraining dataset: {len(train_df)} trades")
    print(f"Saved to: {train_path}")

    print(f"\nTest dataset: {len(test_df)} trades")
    print(f"Saved to: {test_path}")

    print("\nTraining dataset sample:")
    print(train_df.head())

    print("\nTest dataset sample:")
    print(test_df.head())

    print("\nMost common training relationships:")
    print(
        train_df.groupby(
            ["counterparty_id", "portfolio_id"]
        )
        .size()
        .sort_values(ascending=False)
        .head(10)
    )
