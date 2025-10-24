GUIDELINE — Developer & Analyst Notes
=====================================

Purpose
-------
This document explains the code structure, simulation rules, and extension points for analysts or developers who want to modify or extend the Blackjack simulator and CLI trainer.

High-level structure
--------------------
- `BJ.py` — Core simulation and shared agent logic
  - `BlackjackAgent`:
    - draw_card() -> card
    - hand_value(cards) -> (total:int, is_soft:bool)
    - is_blackjack(cards) -> bool
    - dealer_play(dealer_cards, hit_soft_17=True) -> dealer_final_cards
  - `BlackjackAgentBasic`:
    - strategy(player_cards, dealer_up, can_double, can_split_pair, surrender_allowed) -> action_char
    - action_char is one of: 'H','S','D','P','R'
  - `play_hand_once(rules, trackers)` — resolves one initial hand (supports splitting via stack-based approach) and returns outcome(s) as list of tuples [(result, payoff), ...]
  - `simulate(nhands, hit_soft_17, seed)` — runs many hands, aggregates trackers, returns summary and trackers. Uses infinite-deck draw model (random.choice).
  - `make_plots(summary, trackers, save_prefix)` — generates matplotlib plots (imported lazily).

- `cli_blackjack.py` — Interactive trainer
  - Uses `BlackjackAgent` for dealing and `BlackjackAgentBasic`/`basic_strategy` for recommendations.
  - Adds bankroll management and prints strategy recommendations at decision points and after outcome resolution.

Rules implemented in the simulation
----------------------------------
- Infinite-replacement draw model (random.choice from RANKS) — this approximates an infinite shoe.
- Dealer hits until 17. Soft 17 behavior is configurable.
- Blackjack pays 3:2.
- Late surrender allowed (player can surrender on first decision, loses half bet).
- Doubling allowed; simulator supports doubling after split when configured (DAS).
- Splits supported; simulator supports resplits up to `resplit_limit` (default 3).
- No insurance, no side bets, and no card counting infrastructure (unless you add a shoe/deck simulator).

Design notes and rationale
--------------------------
- Infinite-replacement simplifies simulation and avoids tracking a shoe; it's valid for EV analysis of basic strategy but not for card-counting studies.
- Strategy is implemented as a deterministic function that depends only on local hand and dealer upcard. This makes it easy to test and compare actions.
- `play_hand_once` uses a stack to support splitting and resplitting in a controlled, iterative way (avoids recursion depth issues).

Key functions and API for extension
----------------------------------
- To change the draw model to an N-deck shoe:
  - Replace `BlackjackAgent.draw_card()` to draw from a Shoe object that tracks remaining cards.
  - Implement a `Shoe` class with `draw()` and `shuffle()` and inject it into `play_hand_once` and CLI (pass as dependency or global singleton).

- To adjust rules:
  - Update `rules` dict that `simulate` and `play_hand_once` accept. Supported keys include:
    - hit_soft_17 (bool)
    - late_surrender (bool)
    - das (bool)
    - resplit_limit (int)
    - peek (bool)
    - blackjack_3to2 (bool)

- To test strategy decisions:
  - Write unit tests importing `BlackjackAgentBasic.strategy` and assert actions for known hands and dealer upcards.

Testing guidance
----------------
- Add unit tests for:
  - `BlackjackAgent.hand_value()` (soft/hard totals and multiple aces)
  - `BlackjackAgent.is_blackjack()`
  - `BlackjackAgentBasic.strategy()` for various canonical hands
  - `play_hand_once()` with fixed RNG seed and simple `rules` to verify outcomes
- For simulation-level regressions, run `simulate(nhands=10000, seed=...)` and verify that the EV and distribution behavior are stable (within noise) across runs.

Data collectors / trackers
--------------------------
- `trackers` object in `simulate` collects:
  - `outcome`: Counter of 'win', 'loss', 'push', 'blackjack_win', 'blackjack_push', 'surrender', 'dealer_blackjack', 'dealer_bust_win'
  - `counters`: misc counters ('player_bust', 'dealer_bust', 'doubles', 'splits')
  - `player_totals`: distribution of resolved player totals 4..21 (busts counted separately)
  - `dealer_totals`: distribution of resolved dealer totals (17..21 + 'bust')

Performance tips
----------------
- The simulator uses pure Python and random.choice — it's fine for tens/hundreds of thousands of hands. For millions of hands, consider:
  - Using NumPy for vectorized random draws (but you'd need to adapt hand-level logic).
  - Implementing a C-extension or PyPy for faster tight loops.

Extensions and experiments
-------------------------
- Add a `Shoe`/`Deck` implementation to study finite-deck effects and card counting.
- Add logging to CSV during CLI runs to collect training datasets of decisions and outcomes (helpful for ML-based analysis).
- Replace `random.choice` with a seeded RNG passed through the agent to make simulations fully deterministic and easier to reproduce across modules.

Contact
-------
If you want help implementing any of the extensions above — shoe simulation, logging, or unit tests — tell me which one and I'll implement it.
