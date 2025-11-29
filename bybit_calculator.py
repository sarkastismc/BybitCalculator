import math

def liquidation_price(entry_price, leverage, balance, position_size, mmr, side):
    notional = position_size * entry_price
    maintenance_margin = notional * mmr
    initial_margin = notional / leverage

    if side.lower() == "long":
        liq = entry_price - ((balance + initial_margin - maintenance_margin) / position_size)
    else:  # short
        liq = entry_price + ((balance + initial_margin - maintenance_margin) / position_size)

    return liq


def get_float(prompt):
    while True:
        try:
            return float(input(prompt))
        except:
            print("Invalid number. Try again.")


def main():
    print("\n===== BYBIT CALCULATOR =====")
    print("Supports multiple entries, long & short, exact MMR liquidation.\n")

    # LONG or SHORT
    side = ""
    while side.lower() not in ["long", "short"]:
        side = input("Position side (long/short): ")

    # MMR
    mmr = get_float("Maintenance Margin Rate (MMR) (example 0.005): ")

    # Balance
    balance = get_float("Account balance (USDT): ")

    # Number of entries
    n = int(get_float("Number of entries: "))

    entries = []
    total_size = 0
    total_cost = 0

    for i in range(n):
        print(f"\nEntry #{i+1}")
        price = get_float("  Entry price: ")
        size = get_float("  Position size (USDT): ")
        entries.append((price, size))
        total_size += size
        total_cost += price * size

    avg_entry = total_cost / total_size

    leverage = get_float("\nLeverage: ")

    # Calculate liquidation
    liq = liquidation_price(avg_entry, leverage, balance, total_size, mmr, side)

    print("\n===== RESULTS =====")
    print(f"Average Entry Price: {avg_entry:.2f}")
    print(f"Total Position Size: {total_size:.2f} USDT")
    print(f"Liquidation Price:   {liq:.2f}\n")

if __name__ == "__main__":
    main()
