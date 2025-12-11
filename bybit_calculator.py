#!/usr/bin/env python3

def get_float(prompt):
    while True:
        try:
            return float(input(prompt))
        except ValueError:
            print("Invalid number. Try again.")


def get_int(prompt):
    while True:
        try:
            return int(input(prompt))
        except ValueError:
            print("Invalid integer. Try again.")


def compute_base(position_side, mmr, leverage, entries):
    """
    entries: list of dicts with {"entry": price, "im": initial_margin}
    side: 'long' or 'short'
    mmr: maintenance margin rate
    leverage: same leverage used for all entries

    Returns dict with base stats: avg_entry, Q (btc size), IM, NV, MM, base_liq
    """
    side = position_side.lower()
    L = leverage
    m = mmr

    # Compute per-entry notional & size
    sizes = []
    notionals = []
    weighted_sum = 0.0
    for e in entries:
        price = e["entry"]
        im = e["im"]
        notional = im * L
        size = notional / price
        sizes.append(size)
        notionals.append(notional)
        weighted_sum += price * size

    Q0 = sum(sizes)
    NV0 = sum(notionals)
    IM0 = sum(e["im"] for e in entries)

    if Q0 <= 0 or NV0 <= 0:
        return None

    avg0 = weighted_sum / Q0
    MM0 = NV0 * m

    if side == "short":
        base_liq = avg0 + (IM0 - MM0) / Q0
    else:  # long
        base_liq = avg0 - (IM0 - MM0) / Q0

    return {
        "avg_entry": avg0,
        "Q0": Q0,
        "IM0": IM0,
        "NV0": NV0,
        "MM0": MM0,
        "liq0": base_liq,
        "L": L,
        "m": m,
    }


def solve_margin_for_target_liq_short(base, target_liq, entry_new):
    """
    Short side: solve for new initial margin (im) given:
      - target liquidation price T
      - new entry price e (entry_new)
      - same leverage L and mmr m
    Using formula derived from:
      T = Avg1 + (IM1 - MM1)/Q1
    Returns im or None if impossible.
    """
    T = target_liq
    e = entry_new
    L = base["L"]
    m = base["m"]
    Q0 = base["Q0"]
    IM0 = base["IM0"]
    NV0 = base["NV0"]
    avg0 = base["avg_entry"]

    A = avg0 * Q0
    B = Q0
    C = NV0

    numerator = T * B - (A + IM0 - C * m)
    denom = (L + 1 - L * m) - (T * L / e)

    if abs(denom) < 1e-12:
        return None

    im = numerator / denom
    return im


def solve_margin_for_target_liq_long(base, target_liq, entry_new):
    """
    Long side version: solve for im given target liq T and entry_new e.
    """
    T = target_liq
    e = entry_new
    L = base["L"]
    m = base["m"]
    Q0 = base["Q0"]
    IM0 = base["IM0"]
    NV0 = base["NV0"]
    avg0 = base["avg_entry"]

    A = avg0 * Q0
    B = Q0
    C = NV0

    numerator = T * B - (A - IM0 + C * m)
    denom = (L - 1 + L * m) - (T * L / e)

    if abs(denom) < 1e-12:
        return None

    im = numerator / denom
    return im


def solve_entry_for_target_liq_short(base, target_liq, im_new):
    """
    Short side: solve for entry price e given target liq T and new initial margin im_new.
    """
    T = target_liq
    K = im_new  # new IM
    L = base["L"]
    m = base["m"]
    Q0 = base["Q0"]
    IM0 = base["IM0"]
    NV0 = base["NV0"]
    avg0 = base["avg_entry"]

    A = avg0 * Q0
    B = Q0
    C = NV0

    # N0 = A + IM0 + K - C*m - K*L*m
    N0 = A + IM0 + K - C * m - K * L * m
    denom = N0 - T * B

    if abs(denom) < 1e-12:
        return None

    e = T * K * L / denom
    return e


def solve_entry_for_target_liq_long(base, target_liq, im_new):
    """
    Long side: solve for entry price e given target liq T and new initial margin im_new.
    """
    T = target_liq
    K = im_new  # new IM
    L = base["L"]
    m = base["m"]
    Q0 = base["Q0"]
    IM0 = base["IM0"]
    NV0 = base["NV0"]
    avg0 = base["avg_entry"]

    A = avg0 * Q0
    B = Q0
    C = NV0

    # N0 = (A - IM0 + C*m) + K*(L - 1 + L*m)
    N0 = (A - IM0 + C * m) + K * (L - 1 + L * m)
    denom = N0 - T * B

    if abs(denom) < 1e-12:
        return None

    e = T * K * L / denom
    return e


def show_combined_result(base, side, im_new, entry_new, target_liq):
    """
    For information: compute and show the new combined stats with the extra position.
    """
    L = base["L"]
    m = base["m"]

    # Old totals
    Q0 = base["Q0"]
    NV0 = base["NV0"]
    IM0 = base["IM0"]
    avg0 = base["avg_entry"]

    # New position
    notional_new = im_new * L
    size_new = notional_new / entry_new

    # New totals
    Q1 = Q0 + size_new
    NV1 = NV0 + notional_new
    IM1 = IM0 + im_new
    avg1 = (avg0 * Q0 + entry_new * size_new) / Q1
    MM1 = NV1 * m

    if side == "short":
        liq1 = avg1 + (IM1 - MM1) / Q1
    else:
        liq1 = avg1 - (IM1 - MM1) / Q1

    print("\n--- NEW COMBINED POSITION (INFO) ---")
    print(f"New added position: entry={entry_new:.2f}, IM={im_new:.2f}, notional={notional_new:.2f}, size={size_new:.8f} BTC")
    print(f"New average entry:  {avg1:.2f}")
    print(f"New total IM:       {IM1:.2f}")
    print(f"New total notional: {NV1:.2f}")
    print(f"New total size:     {Q1:.8f} BTC")
    print(f"New estimated liq:  {liq1:.2f} (target was {target_liq:.2f})")


def main():
    print("\n===== BYBIT LIQUIDATION PUSH CALCULATOR (ISOLATED, SAME LEVERAGE) =====\n")
    print("This tool assumes:")
    print("  - Isolated margin")
    print("  - All positions same direction (all long OR all short)")
    print("  - Same leverage for existing and new position")
    print("It will compute the extra position needed to move liq to a desired target.\n")

    # 1) Side
    side = ""
    while side.lower() not in ("long", "short"):
        side = input("Current position side (long/short): ").strip().lower()
        if side not in ("long", "short"):
            print("Please type 'long' or 'short'.")

    # 2) MMR
    print("\nMaintenance Margin Rate (MMR) example for BTC:")
    print("  For typical BTC positions: 0.005 (0.5%)")
    mmr = get_float("MMR (e.g. 0.005): ")

    # 3) Leverage (shared)
    leverage = get_float("\nLeverage used (same for all entries, e.g. 2): ")

    # 4) Existing entries
    n = get_int("\nNumber of existing entries in this direction: ")
    entries = []
    for i in range(n):
        print(f"\nExisting Entry #{i + 1}")
        price = get_float("  Entry price (USD): ")
        im = get_float("  Initial margin for this entry (USDT): ")
        entries.append({"entry": price, "im": im})

    base = compute_base(side, mmr, leverage, entries)
    if base is None:
        print("\nSomething went wrong (zero size / notional).")
        input("\nPress Enter to exit...")
        return

    print("\n--- CURRENT POSITION STATS ---")
    print(f"Average entry:   {base['avg_entry']:.2f} USD")
    print(f"Total BTC size:  {base['Q0']:.8f}")
    print(f"Total notional:  {base['NV0']:.2f} USDT")
    print(f"Total IM:        {base['IM0']:.2f} USDT")
    print(f"Current liq:     {base['liq0']:.2f} USD")

    # 5) Target liq
    print("\nEnter the desired (target) liquidation price.")
    if side == "short":
        print("For SHORT, pushing liq 'away' usually means a HIGHER liq price (further above).")
    else:
        print("For LONG, pushing liq 'away' usually means a LOWER liq price (further below).")
    target_liq = get_float("Target liquidation price (USD): ")

    # 6) Choose mode
    print("\nHow do you want to solve this?")
    print("  1) I know the PRICE I want to open the new position at -> calculate REQUIRED initial margin")
    print("  2) I know how much INITIAL MARGIN I want to add -> calculate REQUIRED entry price")
    mode = ""
    while mode not in ("1", "2"):
        mode = input("Choice (1/2): ").strip()

    if mode == "1":
        # User gives entry_new, we solve for IM_new
        entry_new = get_float("\nPrice for NEW position (USD): ")
        if side == "short":
            im_new = solve_margin_for_target_liq_short(base, target_liq, entry_new)
        else:
            im_new = solve_margin_for_target_liq_long(base, target_liq, entry_new)

        if im_new is None or im_new <= 0:
            print("\nNo valid solution for this target/liq at that entry price with same leverage.")
        else:
            print(f"\nRequired INITIAL MARGIN for new position at {entry_new:.2f}: {im_new:.2f} USDT")
            show_combined_result(base, side, im_new, entry_new, target_liq)

    else:
        # mode == "2": user gives IM_new, we solve for entry_new
        im_new = get_float("\nInitial margin (USDT) for NEW position: ")
        if side == "short":
            entry_new = solve_entry_for_target_liq_short(base, target_liq, im_new)
        else:
            entry_new = solve_entry_for_target_liq_long(base, target_liq, im_new)

        if entry_new is None or entry_new <= 0:
            print("\nNo valid entry price solution for this target/liq with that margin and same leverage.")
        else:
            print(f"\nRequired ENTRY PRICE for new position with IM={im_new:.2f}: {entry_new:.2f} USD")
            show_combined_result(base, side, im_new, entry_new, target_liq)

    print("\nDone.")
    input("\nPress Enter to exit...")


if __name__ == "__main__":
    main()
