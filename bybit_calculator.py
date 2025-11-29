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


def compute_summary(entries, side, mmr, tp, sl):
    """
    entries: list of dicts:
      { "entry": float, "im": float, "lev": float, "notional": float, "size_btc": float }
    side: 'long' or 'short'
    mmr: maintenance margin rate
    tp, sl: prices for take profit / stop loss

    Returns a dict with all important values.
    """
    total_notional = sum(e["notional"] for e in entries)
    total_btc = sum(e["size_btc"] for e in entries)

    if total_btc <= 0:
        return None

    # Weighted average entry (by BTC size)
    weighted_sum = sum(e["entry"] * e["size_btc"] for e in entries)
    avg_entry = weighted_sum / total_btc

    # Total initial margin and maintenance margin
    total_im = sum(e["im"] for e in entries)
    maintenance_margin = total_notional * mmr

    # Estimated isolated liquidation price (simplified, no fee buffer)
    if side == "short":
        liq_price = avg_entry + (total_im - maintenance_margin) / total_btc
    else:  # long
        liq_price = avg_entry - (total_im - maintenance_margin) / total_btc

    # PnL at TP and SL
    if side == "short":
        pnl_tp = (avg_entry - tp) * total_btc
        pnl_sl = (avg_entry - sl) * total_btc
    else:  # long
        pnl_tp = (tp - avg_entry) * total_btc
        pnl_sl = (sl - avg_entry) * total_btc

    # percentage moves from avg entry
    move_tp_pct = ((tp - avg_entry) / avg_entry) * 100.0
    move_sl_pct = ((sl - avg_entry) / avg_entry) * 100.0

    # risk : reward (use absolute values)
    risk = abs(pnl_sl)
    reward = abs(pnl_tp)
    if risk > 0:
        rr = reward / risk
        rr_text = f"{rr:.2f} : 1"
    else:
        rr_text = "N/A"

    return {
        "total_notional": total_notional,
        "total_btc": total_btc,
        "avg_entry": avg_entry,
        "total_im": total_im,
        "maintenance_margin": maintenance_margin,
        "liq_price": liq_price,
        "pnl_tp": pnl_tp,
        "pnl_sl": pnl_sl,
        "move_tp_pct": move_tp_pct,
        "move_sl_pct": move_sl_pct,
        "rr_text": rr_text,
        "tp": tp,
        "sl": sl,
    }


def print_summary(summary, side, label="RESULTS"):
    """Pretty print a summary block."""
    print(f"\n===== {label} =====")
    print(f"Side:                 {side.upper()}")
    print(f"Total initial margin: {summary['total_im']:.2f} USDT")
    print(f"Total notional:       {summary['total_notional']:.2f} USDT")
    print(f"Total BTC size:       {summary['total_btc']:.8f} BTC")
    print(f"Average entry price:  {summary['avg_entry']:.2f} USD")
    print(f"Maintenance margin:   {summary['maintenance_margin']:.2f} USDT")
    print(f"Estimated liq price:  {summary['liq_price']:.2f} USD")

    print("\n--- TP / SL Analysis ---")
    print(f"TP price:             {summary['tp']:.2f} USD")
    print(f"  PnL at TP:          {summary['pnl_tp']:.2f} USDT")
    print(f"  Move from entry:    {summary['move_tp_pct']:.2f}%")

    print(f"\nSL price:             {summary['sl']:.2f} USD")
    print(f"  PnL at SL:          {summary['pnl_sl']:.2f} USDT")
    print(f"  Move from entry:    {summary['move_sl_pct']:.2f}%")

    print(f"\nRisk / Reward ratio (|TP| : |SL|): {summary['rr_text']}")


def main():
    print("\n===== BYBIT ISOLATED CALCULATOR (IM-BASED) =====\n")
    print("This version uses:")
    print("  - Initial margin + leverage for each entry")
    print("  - Calculates notional, BTC size, average entry")
    print("  - Estimates isolated liquidation price (no fees/buffers)")
    print("  - Calculates PnL for Take Profit (TP) and Stop Loss (SL)")
    print("  - Allows adding more positions AFTER seeing initial results\n")

    # 1) Side: long or short
    side = ""
    while side.lower() not in ("long", "short"):
        side = input("Position side (long/short): ").strip().lower()
        if side not in ("long", "short"):
            print("Please type 'long' or 'short'.")

    # 2) MMR (maintenance margin rate)
    print("\nMaintenance Margin Rate (MMR) example for BTC:")
    print("  - For your position sizes, use 0.005 (0.5%)")
    mmr = get_float("MMR (example 0.005): ")

    # 3) Number of entries
    n = get_int("\nNumber of entries (e.g. 1, 2, 3): ")

    entries = []
    for i in range(n):
        print(f"\nEntry #{i + 1}")
        entry_price = get_float("  Entry price (USD): ")
        im = get_float("  Initial margin (USDT): ")
        lev = get_float("  Leverage (e.g. 2): ")

        notional = im * lev
        size_btc = notional / entry_price

        entries.append({
            "entry": entry_price,
            "im": im,
            "lev": lev,
            "notional": notional,
            "size_btc": size_btc
        })

    # 4) Ask for TP and SL once (we will reuse for all recalculations)
    print("\nNow enter your Take Profit and Stop Loss levels.")
    print("For SHORT: TP < avg_entry, SL > avg_entry (usually).")
    print("For LONG:  TP > avg_entry, SL < avg_entry (usually).")

    tp = get_float("Take Profit price (USD): ")
    sl = get_float("Stop Loss price  (USD): ")

    # 5) First summary (base state)
    summary = compute_summary(entries, side, mmr, tp, sl)
    if summary is None:
        print("\nTotal BTC size is zero or negative. Something went wrong.")
        input("\nPress Enter to exit...")
        return

    print_summary(summary, side, label="BASE RESULTS")

    # Store last summary for comparison in the loop
    last_summary = summary

    # 6) Loop: allow adding more positions and recalculating
    while True:
        ans = input("\nDo you want to ADD more positions and recalculate? (y/n): ").strip().lower()
        if not ans.startswith("y"):
            break

        extra_n = get_int("How many additional entries do you want to add now?: ")

        for i in range(extra_n):
            print(f"\nAdditional Entry #{i + 1}")
            entry_price = get_float("  Entry price (USD): ")
            im = get_float("  Initial margin (USDT): ")
            lev = get_float("  Leverage (e.g. 2): ")

            notional = im * lev
            size_btc = notional / entry_price

            entries.append({
                "entry": entry_price,
                "im": im,
                "lev": lev,
                "notional": notional,
                "size_btc": size_btc
            })

        # Recompute after adding new positions
        new_summary = compute_summary(entries, side, mmr, tp, sl)
        if new_summary is None:
            print("\nAfter adding, total BTC size is zero or negative. Something went wrong.")
            input("\nPress Enter to exit...")
            return

        # Print updated results
        print_summary(new_summary, side, label="UPDATED RESULTS AFTER ADDING POSITIONS")

        # Show comparison vs previous state
        print("\n--- COMPARISON WITH PREVIOUS STATE ---")
        print(f"Average entry:   {last_summary['avg_entry']:.2f}  ->  {new_summary['avg_entry']:.2f}")
        print(f"Liq price:       {last_summary['liq_price']:.2f}  ->  {new_summary['liq_price']:.2f}")
        print(f"PnL at TP:       {last_summary['pnl_tp']:.2f} USDT  ->  {new_summary['pnl_tp']:.2f} USDT")
        print(f"PnL at SL:       {last_summary['pnl_sl']:.2f} USDT  ->  {new_summary['pnl_sl']:.2f} USDT")
        print(f"Risk/Reward:     {last_summary['rr_text']}  ->  {new_summary['rr_text']}")

        # Update last_summary for possible next iteration
        last_summary = new_summary

    print("\nDone.")
    input("\nPress Enter to exit...")


if __name__ == "__main__":
    main()
