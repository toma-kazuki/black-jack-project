BlackJack — Quick Start (User)
===============================

What this is
------------
A simple terminal Blackjack trainer and simulator. Play rounds in the terminal against a dealer and get basic-strategy recommendations to help you learn.

Quick rules (what you need to know to play)
------------------------------------------
- Goal: get as close to 21 without going over. Face cards (J/Q/K) = 10, A = 1 or 11.
- Dealer shows one upcard. You make decisions (Hit, Stand, Double, Split, Surrender).
- Blackjack (Ace + 10-value on initial two cards) pays 3:2.
- Basic strategy recommendations are shown during play and after each round.

How to run the interactive trainer
----------------------------------
1. Open a terminal in this project folder.
2. Run:

```bash
python3 cli_blackjack.py
```

3. Enter your starting bankroll and the dealer bankroll when prompted. Default bet per round is $10.
4. Use these controls during play:
   - h: hit
   - s: stand
   - d: double
   - p: split
   - r: surrender
   - ?: show the basic strategy recommendation for the current hand
   - q: quit

What the interface shows
------------------------
- Player and dealer hands and totals. Soft totals are marked.
- After each round, the program prints the basic-strategy recommendation for the last decision point so you can compare.
- Balances for player and dealer are updated after each round.

Notes
-----
- This trainer uses an infinite-deck style draw (random draws with replacement). It is designed for learning strategy more than for card-counting practice.
- For developers or analysts who want implementation details, see `GUIDELINE.md`.

*** End of User README ***
