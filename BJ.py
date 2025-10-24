import random
from collections import Counter, defaultdict
import argparse
# matplotlib is imported lazily inside make_plots to avoid a hard dependency at import time

# ---------- Config via CLI ----------
def parse_args():
    p = argparse.ArgumentParser(description="Monte Carlo Blackjack with distributions & plots")
    p.add_argument("-n", "--hands", type=int, default=300_000, help="Number of initial hands to simulate")
    p.add_argument("--s17", action="store_true", help="Use S17 (dealer stands on soft 17). Default is H17.")
    p.add_argument("--seed", type=int, default=7, help="RNG seed for reproducibility")
    p.add_argument("--save-prefix", default="bj_", help="Filename prefix for saved plots")
    return p.parse_args()

# ---------- Cards & Hand Utilities ----------
RANKS = [2,3,4,5,6,7,8,9,10,'J','Q','K','A']


class BlackjackAgent:
    """Agent that encapsulates card utilities and basic strategy recommendations.

    This class mirrors the existing module-level functions so they can be reused
    by both the simulation and a new CLI interactive game.
    """
    def __init__(self, rng_seed=None):
        if rng_seed is not None:
            random.seed(rng_seed)

    @staticmethod
    def draw_card():
        return random.choice(RANKS)

    @staticmethod
    def hand_value(cards):
        total = sum(10 if c in ('J','Q','K') else (1 if c=='A' else c) for c in cards)
        aces = cards.count('A')
        is_soft = False
        while aces > 0 and total + 10 <= 21:
            total += 10
            is_soft = True
            aces -= 1
        return total, is_soft

    @staticmethod
    def is_blackjack(cards):
        return len(cards) == 2 and BlackjackAgent.hand_value(cards)[0] == 21

    def dealer_play(self, dealer_cards, hit_soft_17=True):
        while True:
            total, soft = BlackjackAgent.hand_value(dealer_cards)
            if total < 17 or (total == 17 and soft and hit_soft_17):
                dealer_cards.append(BlackjackAgent.draw_card())
            else:
                break
        return dealer_cards

# ---------- Basic Strategy (approx image chart: H17 DAS LS) ----------
def basic_strategy(player, dealer_up, can_double, can_split_pair, surrender_allowed):
    # keep module-level basic_strategy for backwards compatibility but delegate to agent
    return BlackjackAgentBasic.strategy(player, dealer_up, can_double, can_split_pair, surrender_allowed)


class BlackjackAgentBasic:
    """Static basic strategy helper used by both the agent and the module functions."""
    @staticmethod
    def strategy(player, dealer_up, can_double, can_split_pair, surrender_allowed):
        up = dealer_up
        upv = 10 if up in ('J','Q','K') else (11 if up=='A' else up)
        total, soft = BlackjackAgent.hand_value(player)

        # Late surrender
        if surrender_allowed and len(player)==2 and not soft:
            if total==16 and upv in (9,10,11): return 'R'
            if total==15 and upv==10: return 'R'

        # Pairs (only identical ranks are split)
        if can_split_pair and len(player)==2 and player[0]==player[1]:
            v = 11 if player[0]=='A' else (10 if player[0] in ('J','Q','K') else player[0])
            if v==11: return 'P'              # A,A
            if v==9:  return 'P' if upv in (2,3,4,5,6,8,9) else 'S'
            if v==8:  return 'P'
            if v==7:  return 'P' if upv in range(2,8) else 'H'
            if v==6:  return 'P' if upv in range(2,7) else 'H'
            if v==4:  return 'P' if upv in (5,6) else 'H'
            if v in (2,3): return 'P' if upv in range(2,8) else 'H'
            if v==5:  return 'D' if can_double and upv in range(2,10) else 'H'
            if v==10: return 'S'              # 10s

        # Soft totals
        if soft:
            if total in (13,14): return 'D' if can_double and upv in (5,6) else 'H'
            if total in (15,16): return 'D' if can_double and upv in (4,5,6) else 'H'
            if total==17:        return 'D' if can_double and upv in (3,4,5,6) else ('S' if upv<=8 else 'H')
            if total==18:
                if can_double and upv in (3,4,5,6): return 'D'
                return 'S' if upv in (2,7,8) else 'H'
            if total>=19: return 'S'

        # Hard totals
        if total <= 8:  return 'H'
        if total == 9:  return 'D' if can_double and upv in (3,4,5,6) else 'H'
        if total == 10: return 'D' if can_double and upv in range(2,10) else 'H'
        if total == 11: return 'D' if can_double else 'H'
        if total == 12: return 'S' if upv in (4,5,6) else 'H'
        if 13 <= total <= 16: return 'S' if upv in (2,3,4,5,6) else 'H'
        return 'S'  # 17+


# Module-level wrappers for backwards compatibility
def draw_card():
    return BlackjackAgent.draw_card()


def hand_value(cards):
    return BlackjackAgent.hand_value(cards)


def is_blackjack(cards):
    return BlackjackAgent.is_blackjack(cards)


def dealer_play(dealer_cards, hit_soft_17=True):
    return BlackjackAgent().dealer_play(dealer_cards, hit_soft_17)

# ---------- One Hand Simulation ----------
def play_hand_once(rules, trackers):
    hit_soft_17 = rules.get("hit_soft_17", True)
    late_surrender = rules.get("late_surrender", True)
    das = rules.get("das", True)
    resplit_limit = rules.get("resplit_limit", 3)
    peek = rules.get("peek", True)
    blackjack_3to2 = rules.get("blackjack_3to2", True)

    player = [draw_card(), draw_card()]
    dealer = [draw_card(), draw_card()]
    dealer_up = dealer[0]

    dealer_blackjack = is_blackjack(dealer)
    player_blackjack = is_blackjack(player)

    # Dealer peek for blackjack
    if peek and dealer_up in (10,'J','Q','K','A') and dealer_blackjack:
        if player_blackjack:
            trackers['outcome']['blackjack_push'] += 1
            trackers['outcome']['push'] += 1
            return [('push', 0)]
        trackers['outcome']['loss'] += 1
        trackers['outcome']['dealer_blackjack'] += 1
        return [('loss', -1)]

    if player_blackjack:
        trackers['outcome']['blackjack_win'] += 1
        trackers['outcome']['win'] += 1
        return [('win', 1.5 if blackjack_3to2 else 1.2)]

    outcomes = []
    stack = [(player, 1.0, 0, True)]
    while stack:
        cards, bet, splits_done, can_double = stack.pop()
        surrendered = False

        while True:
            can_split_pair = (len(cards)==2 and cards[0]==cards[1] and splits_done < resplit_limit)
            action = basic_strategy(cards, dealer_up, can_double, can_split_pair, late_surrender)
            if action == 'R':
                trackers['outcome']['surrender'] += 1
                trackers['outcome']['loss'] += 1
                outcomes.append(('loss', -0.5*bet))
                surrendered = True
                break
            elif action == 'P' and can_split_pair:
                c = cards[0]
                hand1, hand2 = [c, draw_card()], [c, draw_card()]
                stack.append((hand2, bet, splits_done+1, das))
                cards = hand1
                can_double = das
                trackers['counters']['splits'] += 1
                continue
            elif action == 'D' and can_double:
                cards.append(draw_card())
                bet *= 2
                trackers['counters']['doubles'] += 1
                break
            elif action == 'H':
                cards.append(draw_card())
                total, _ = hand_value(cards)
                if total > 21:
                    trackers['outcome']['loss'] += 1
                    trackers['counters']['player_bust'] += 1
                    outcomes.append(('loss', -bet))
                    break
                can_double = False
                continue
            else:  # Stand
                break

        if surrendered:
            continue

        total, _ = hand_value(cards)
        # track player total bins
        if total > 21:
            pass
        else:
            trackers['player_totals'][total] += 1

        if total <= 21:
            dealer_final = dealer_play(dealer[:], hit_soft_17)
            dtotal, _ = hand_value(dealer_final)
            # track dealer total bins
            if dtotal > 21:
                trackers['counters']['dealer_bust'] += 1
                trackers['dealer_totals']['bust'] += 1
            else:
                trackers['dealer_totals'][max(17, dtotal)] += 1  # 17..21 only appear

            if dtotal > 21 or total > dtotal:
                trackers['outcome']['win'] += 1
                if dtotal > 21:
                    trackers['outcome']['dealer_bust_win'] += 1
                outcomes.append(('win', bet))
            elif total < dtotal:
                trackers['outcome']['loss'] += 1
                outcomes.append(('loss', -bet))
            else:
                trackers['outcome']['push'] += 1
                outcomes.append(('push', 0))
    return outcomes

# ---------- Simulation Driver ----------
def simulate(nhands=300_000, hit_soft_17=True, seed=7):
    random.seed(seed)
    rules = dict(hit_soft_17=hit_soft_17, late_surrender=True, das=True,
                 resplit_limit=3, peek=True, blackjack_3to2=True)

    trackers = {
        'outcome': Counter(),
        'counters': Counter(),
        'player_totals': Counter(),   # 4..21 (only resolved hands that didn't bust)
        'dealer_totals': Counter()    # 17..21 + 'bust'
    }

    total_units = 0.0
    for _ in range(nhands):
        for result, payoff in play_hand_once(rules, trackers):
            total_units += payoff

    total_resolved = trackers['outcome']['win'] + trackers['outcome']['loss'] + trackers['outcome']['push']
    ev = total_units / nhands

    summary = {
        "hands_simulated": nhands,
        "rule": "S17" if not hit_soft_17 else "H17",
        "win_rate": trackers['outcome']['win']/total_resolved if total_resolved else 0,
        "loss_rate": trackers['outcome']['loss']/total_resolved if total_resolved else 0,
        "push_rate": trackers['outcome']['push']/total_resolved if total_resolved else 0,
        "ev_per_initial_bet": ev,
    }
    return summary, trackers

# ---------- Plotting ----------
def make_plots(summary, trackers, save_prefix):
    import matplotlib.pyplot as plt

    # Outcome distribution bar
    outcome_keys = ["win", "loss", "push", "surrender", "blackjack_win", "blackjack_push", "dealer_bust_win"]
    vals = [trackers['outcome'][k] for k in outcome_keys]
    total = sum(vals) if sum(vals) else 1
    probs = [v/total for v in vals]

    plt.figure()
    plt.bar(outcome_keys, probs)
    plt.title(f"Outcome Probability Distribution ({summary['rule']})")
    plt.ylabel("Probability")
    plt.xticks(rotation=30, ha="right")
    plt.tight_layout()
    fname1 = f"{save_prefix}outcomes_{summary['rule']}.png"
    plt.savefig(fname1, dpi=160)
    
    print(f"Saved: {fname1}")

    # Player totals distribution (4..21 plus implicit bust via counters)
    player_bins = list(range(4,22))
    pvals = [trackers['player_totals'][b] for b in player_bins]
    ptotal = sum(pvals) + trackers['counters']['player_bust']
    pprobs = [v/ptotal for v in pvals]
    plt.figure()
    plt.bar([str(b) for b in player_bins] + ["Bust"], pprobs + [trackers['counters']['player_bust']/ptotal if ptotal else 0])
    plt.title(f"Player Final Total Distribution ({summary['rule']})")
    plt.ylabel("Probability")
    plt.tight_layout()
    fname2 = f"{save_prefix}player_totals_{summary['rule']}.png"
    plt.savefig(fname2, dpi=160)
    
    print(f"Saved: {fname2}")

    # Dealer totals distribution (17..21 + bust)
    dealer_bins = ["17","18","19","20","21","Bust"]
    dvals = [trackers['dealer_totals'][17], trackers['dealer_totals'][18],
             trackers['dealer_totals'][19], trackers['dealer_totals'][20],
             trackers['dealer_totals'][21], trackers['dealer_totals']['bust']]
    dtotal = sum(dvals) if sum(dvals) else 1
    dprobs = [v/dtotal for v in dvals]
    plt.figure()
    plt.bar(dealer_bins, dprobs)
    plt.title(f"Dealer Final Total Distribution ({summary['rule']})")
    plt.ylabel("Probability")
    plt.tight_layout()
    fname3 = f"{save_prefix}dealer_totals_{summary['rule']}.png"
    plt.savefig(fname3, dpi=160)
    
    print(f"Saved: {fname3}")

    # show plots if running interactively
    try:
        plt.show()
    except Exception:
        pass

# ---------- Main ----------
def main():
    args = parse_args()
    summary, trackers = simulate(nhands=args.hands, hit_soft_17=not args.s17, seed=args.seed)

    print(f"\nRule: {summary['rule']}")
    print(f"Hands simulated: {summary['hands_simulated']}")
    print(f"Win:  {summary['win_rate']*100:.2f}%")
    print(f"Loss: {summary['loss_rate']*100:.2f}%")
    print(f"Push: {summary['push_rate']*100:.2f}%")
    print(f"EV per initial bet: {summary['ev_per_initial_bet']*100:.3f}%")

    make_plots(summary, trackers, save_prefix=args.save_prefix)

if __name__ == "__main__":
    main()
    
