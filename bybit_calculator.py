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


def main():
    print("\n===== BYBIT ISOLATED CALCULATOR (IM-BASED) =====\n")
    print("This version uses:")
    print("  - Initial margin + leverage for each entry")
    print("  - Calculates notional, BTC size, average entry")
    print("  - Estimates isolated liquidation price (no fees/buffers)")
    print("  - Calculates PnL for Take Profit (TP) and Stop Loss (SL)\n")

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
    total_notional = 0.0
    total_btc = 0.0

    for i in range(n):
        print(f"\nEntry #{i + 1}")
        entry_price = get_float("  Entry price (USD): ")
        im = get_float("  Initial margin (USDT): ")
        lev = get_float("  Leverage (e.g. 2): ")

        # notional value in USDT
        notional = im * lev
        # BTC size
        size_btc = notional / entry_price

        entries.append({
            "entry": entry_price,
            "im": im,
            "lev": lev,
            "notional": notional,
            "size_btc": size_btc
        })

        total_notional += notional
        total_btc += size_btc

    if total_btc <= 0:
        print("\nTotal BTC size is zero or negative. Something went wrong.")
        input("\nPress Enter to exit...")
        return

    # 4) Weighted average entry (by BTC size)
    weighted_sum = sum(e["entry"] * e["size_btc"] for e in entries)
    avg_entry = weighted_sum / total_btc

    # 5) Total initial margin and maintenance margin
    total_im = sum(e["im"] for e in entries)
    maintenance_margin = total_notional * mmr

    # 6) Isolated liquidation price (simplified, no fee buffer)
    if side == "short":
        liq_price = avg_entry + (total_im - maintenance_margin) / total_btc
    else:  # long
        liq_price = avg_entry - (total_im - maintenance_margin) / total_btc

    # 7) Ask for TP and SL
    print("\nNow enter your Take Profit and Stop Loss levels.")
    print("For SHORT: TP < avg_entry, SL > avg_entry (usually).")
    print("For LONG:  TP > avg_entry, SL < avg_entry (usually).")

    tp = get_float("Take Profit price (USD): ")
    sl = get_float("Stop Loss price  (USD): ")

    # 8) PnL calculations
    # For long:  PnL = (price - avg_entry) * Q
    # For short: PnL = (avg_entry - price) * Q
    if side == "short":
        pnl_tp = (avg_entry - tp) * total_btc
        pnl_sl = (avg_entry - sl) * total_btc
    else:  # long
        pnl_tp = (tp - avg_entry) * total_btc
        pnl_sl = (sl - avg_entry) * total_btc

    # percentage moves from avg entry
    move_tp_pct = ((tp - avg_entry) / avg_entry) * 100.0
    move_sl_pct = ((sl - avg_entry) / avg_entry) * 100.0

    # risk : reward (use absolute values, avoid division by zero)
    risk = abs(pnl_sl)
    reward = abs(pnl_tp)
    rr_text = "N/A"
    if risk > 0:
        rr = reward / risk
        rr_text = f"{rr:.2f} : 1"

    # 9) Print results
    print("\n===== RESULTS =====")
    print(f"Side:                 {side.upper()}")
    print(f"MMR:                  {mmr:.6f}")
    print(f"Total initial margin: {total_im:.2f} USDT")
    print(f"Total notional:       {total_notional:.2f} USDT")
    print(f"Total BTC size:       {total_btc:.8f} BTC")
    print(f"Average entry price:  {avg_entry:.2f} USD")
    print(f"Maintenance margin:   {maintenance_margin:.2f} USDT")
    print(f"Estimated liq price:  {liq_price:.2f} USD")

    print("\n--- TP / SL Analysis ---")
    print(f"TP price:             {tp:.2f} USD")
    print(f"  PnL at TP:          {pnl_tp:.2f} USDT")
    print(f"  Move from entry:    {move_tp_pct:.2f}%")

    print(f"\nSL price:             {sl:.2f} USD")
    print(f"  PnL at SL:          {pnl_sl:.2f} USDT")
    print(f"  Move from entry:    {move_sl_pct:.2f}%")

    print(f"\nRisk / Reward ratio (|TP| : |SL|): {rr_text}")

    print("\nDone.")
    input("\nPress Enter to exit...")


if __name__ == "__main__":
    main()
