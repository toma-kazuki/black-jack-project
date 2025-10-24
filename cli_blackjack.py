#!/usr/bin/env python3
"""Terminal Blackjack interactive game using BlackjackAgent from BJ.py

Controls:
 - h: hit
 - s: stand
 - d: double
 - p: split (if possible)
 - r: surrender (if allowed)
 - ? : show basic strategy recommendation
 - q: quit

This script uses the agent logic in BJ.py for dealing and recommendations.
"""
import sys
import time
import shutil
import random
from BJ import BlackjackAgent, basic_strategy, hand_value, is_blackjack

agent = BlackjackAgent()

RULES = dict(hit_soft_17=True, late_surrender=True, das=True, resplit_limit=3, peek=True, blackjack_3to2=True)

DEFAULT_BET = 10.0


def card_str(card):
    return str(card)


def show_hand(label, cards):
    total, soft = hand_value(cards)
    s = f"{label}: {' '.join(map(card_str, cards))}  -> {total}{' (soft)' if soft else ''}"
    print(s)


def recommend(player_cards, dealer_up):
    # can_double if only 2 cards
    can_double = len(player_cards) == 2
    can_split = len(player_cards) == 2 and player_cards[0] == player_cards[1]
    action = basic_strategy(player_cards, dealer_up, can_double, can_split, RULES['late_surrender'])
    mapping = {'H':'Hit', 'S':'Stand', 'D':'Double', 'P':'Split', 'R':'Surrender'}
    return mapping.get(action, 'Stand')


def fancy_win_display(payout, title=None):
    """Print a flashy, animated win banner with confetti and payout info.

    Works in most modern terminals using ANSI escape codes. Short sleeps
    create a simple animation. Keeps output safe if terminal width can't
    be determined.
    """
    # ANSI helpers
    RESET = "\033[0m"
    BOLD = "\033[1m"
    FG_YEL = "\033[33m"
    FG_GREEN = "\033[32m"
    FG_MAG = "\033[35m"
    BG_YEL = "\033[43m"

    try:
        cols = shutil.get_terminal_size().columns
    except Exception:
        cols = 80

    # small confetti animation
    confetti_chars = ['*','✦','✶','✺','•','🎉']
    for _ in range(6):
        line = ''.join(random.choice(confetti_chars + [' ']*6) for _ in range(cols))
        color = random.choice([FG_YEL, FG_MAG, FG_GREEN])
        print(color + line + RESET)
        time.sleep(0.05)

    # banner text
    title = title or 'YOU WIN!'
    payout_text = f"Payout: ${payout:.2f}"

    # create centered banner lines
    banner_lines = [f"{BOLD}{FG_GREEN}╔{'═'*(min(cols-4, len(payout_text)+20))}╗{RESET}",
                    f"{BOLD}{FG_GREEN}║{' ' * (min(cols-6, len(payout_text)+18))}║{RESET}",
                    f"{BOLD}{FG_YEL}{title.center(min(cols-6, len(payout_text)+18))}{RESET}",
                    f"{BOLD}{FG_MAG}{payout_text.center(min(cols-6, len(payout_text)+18))}{RESET}",
                    f"{BOLD}{FG_GREEN}╚{'═'*(min(cols-4, len(payout_text)+20))}╝{RESET}"]

    # Print a small entrance animation for the banner
    for i in range(1, len(banner_lines)+1):
        print('\n'.join(banner_lines[:i]))
        time.sleep(0.08)

    # final celebratory confetti
    for _ in range(3):
        line = ''.join(random.choice(confetti_chars + [' ']*4) for _ in range(cols))
        print(FG_YEL + line + RESET)
        time.sleep(0.06)



def play_round(player_bank, dealer_bank, bet=DEFAULT_BET):
    """Play one round and return updated (player_bank, dealer_bank).

    Bets are posted at the start: player_bank decreases by bet and dealer_bank increases by bet.
    Payouts later transfer money from dealer_bank back to player_bank.
    """
    # Check funds
    if player_bank < bet:
        print(f"Insufficient funds to bet ${bet:.2f}. You have ${player_bank:.2f}.")
        return player_bank, dealer_bank
    if dealer_bank < 0:
        print("Dealer has no funds to play.")
        return player_bank, dealer_bank

    # Post the initial bet
    player_bank -= bet
    dealer_bank += bet
    current_bet = bet

    player = [agent.draw_card(), agent.draw_card()]
    dealer = [agent.draw_card(), agent.draw_card()]
    dealer_up = dealer[0]

    print("\n--- New Round ---")
    print(f"Player bank: ${player_bank:.2f}  |  Dealer bank: ${dealer_bank:.2f}")
    show_hand('Dealer up', [dealer_up])
    show_hand('Player', player)

    # Immediate blackjack checks
    if is_blackjack(dealer):
        print("Dealer has blackjack")
        if is_blackjack(player):
            print("Push (both blackjack)")
            # return stake to player
            player_bank += current_bet
            dealer_bank -= current_bet
            # show recommendation for final hand
            print("Basic strategy would have recommended:", recommend(player, dealer_up))
            return player_bank, dealer_bank
        else:
            print("Dealer wins")
            # dealer keeps the stake
            print("Basic strategy would have recommended:", recommend(player, dealer_up))
            return player_bank, dealer_bank
    if is_blackjack(player):
        payout = 2.5 * current_bet
        fancy_win_display(payout, title='BLACKJACK!')
        player_bank += payout
        dealer_bank -= payout
        print("Basic strategy would have recommended:", recommend(player, dealer_up))
        return player_bank, dealer_bank

    doubled = False

    # record last decision snapshot (player cards, dealer_up) before each input
    last_decision = (player.copy(), dealer_up)

    while True:
        total, _ = hand_value(player)
        if total > 21:
            print("You busted!")
            # player already lost stake
            # show what basic strategy would have recommended at the last decision point
            print("At your last decision point your hand was:", ' '.join(map(card_str, last_decision[0])), "vs dealer", last_decision[1])
            print("Basic strategy would have recommended:", recommend(last_decision[0], last_decision[1]))
            return player_bank, dealer_bank

        # update snapshot before prompting
        last_decision = (player.copy(), dealer_up)

        cmd = input("Action ([h]it [s]tand [d]ouble [p]split [r]surrender [?]recommend [q]quit): ").strip().lower()
        if cmd == '?':
            print("Recommendation:", recommend(player, dealer_up))
            continue
        if cmd == 'q':
            sys.exit(0)
        if cmd == 'h':
            player.append(agent.draw_card())
            show_hand('Player', player)
            continue
        if cmd == 's':
            break
        if cmd == 'd' and len(player) == 2:
            # Need additional bet
            if player_bank < current_bet:
                print("Insufficient funds to double.")
                continue
            player_bank -= current_bet
            dealer_bank += current_bet
            current_bet *= 2
            player.append(agent.draw_card())
            doubled = True
            show_hand('Player', player)
            break
        if cmd == 'p' and len(player) == 2 and player[0] == player[1]:
            # Single split implementation: deduct extra bet and play each hand separately
            if player_bank < current_bet:
                print("Insufficient funds to split.")
                continue
            player_bank -= current_bet
            dealer_bank += current_bet
            card = player[0]
            hand1 = [card, agent.draw_card()]
            hand2 = [card, agent.draw_card()]
            print("Playing split hands")
            print("Hand 1:")
            p_delta1, d_delta1 = play_subhand(hand1, dealer, current_bet)
            print("Hand 2:")
            p_delta2, d_delta2 = play_subhand(hand2, dealer, current_bet)
            # Apply returned deltas
            player_bank += p_delta1 + p_delta2
            dealer_bank += d_delta1 + d_delta2
            return player_bank, dealer_bank
        if cmd == 'r' and len(player) == 2:
            # Surrender: return half the stake
            print("You surrendered. Lose half your bet.")
            refund = current_bet / 2.0
            player_bank += refund
            dealer_bank -= refund
            return player_bank, dealer_bank
        print("Invalid command or not allowed now")

    # Dealer plays
    dealer_final = agent.dealer_play(dealer[:], RULES['hit_soft_17'])
    show_hand('Dealer final', dealer_final)
    ptotal, _ = hand_value(player)
    dtotal, _ = hand_value(dealer_final)
    if dtotal > 21 or ptotal > dtotal:
        # Player wins: pays 2x current_bet (returns stake + winnings)
        payout = 2.0 * current_bet
        fancy_win_display(payout)
        player_bank += payout
        dealer_bank -= payout
        # show recommendation for the decision point
        print("At your last decision point your hand was:", ' '.join(map(card_str, last_decision[0])), "vs dealer", last_decision[1])
        print("Basic strategy would have recommended:", recommend(last_decision[0], last_decision[1]))
    elif ptotal < dtotal:
        print("You lose")
        # player already lost stake
        print("At your last decision point your hand was:", ' '.join(map(card_str, last_decision[0])), "vs dealer", last_decision[1])
        print("Basic strategy would have recommended:", recommend(last_decision[0], last_decision[1]))
    else:
        print("Push")
        # return stake
        player_bank += current_bet
        dealer_bank -= current_bet
        print("At your last decision point your hand was:", ' '.join(map(card_str, last_decision[0])), "vs dealer", last_decision[1])
        print("Basic strategy would have recommended:", recommend(last_decision[0], last_decision[1]))

    return player_bank, dealer_bank


def play_subhand(hand, dealer, per_hand_bet):
    """Play a split hand separately and return (player_bank_delta, dealer_bank_delta).

    Note: bets for the split hand are assumed to have been posted already (player_bank and dealer_bank adjusted),
    so returned deltas are payout transfers to/from player/dealer.
    """
    show_hand('Player', hand)
    # snapshot for this subhand
    last_decision = (hand.copy(), dealer[0])
    while True:
        total, _ = hand_value(hand)
        if total > 21:
            print("Busted")
            # player already lost the per_hand_bet
            print("At your last decision point your hand was:", ' '.join(map(card_str, last_decision[0])), "vs dealer", last_decision[1])
            print("Basic strategy would have recommended:", recommend(last_decision[0], last_decision[1]))
            return 0.0, 0.0
        # update snapshot before prompting
        last_decision = (hand.copy(), dealer[0])
        cmd = input("Action for split hand ([h]it [s]tand [?]recommend): ").strip().lower()
        if cmd == '?':
            print("Recommendation:", recommend(hand, dealer[0]))
            continue
        if cmd == 'h':
            hand.append(agent.draw_card())
            show_hand('Player', hand)
            continue
        if cmd == 's':
            break
        print("Invalid")
    dealer_final = agent.dealer_play(dealer[:], RULES['hit_soft_17'])
    show_hand('Dealer final', dealer_final)
    ptotal, _ = hand_value(hand)
    dtotal, _ = hand_value(dealer_final)
    if dtotal > 21 or ptotal > dtotal:
        payout = 2.0 * per_hand_bet
        fancy_win_display(payout)
        print("At your last decision point your hand was:", ' '.join(map(card_str, last_decision[0])), "vs dealer", last_decision[1])
        print("Basic strategy would have recommended:", recommend(last_decision[0], last_decision[1]))
        return payout, -payout
    elif ptotal < dtotal:
        print("You lose this hand")
        print("At your last decision point your hand was:", ' '.join(map(card_str, last_decision[0])), "vs dealer", last_decision[1])
        print("Basic strategy would have recommended:", recommend(last_decision[0], last_decision[1]))
        return 0.0, 0.0
    else:
        print("Push")
        print("At your last decision point your hand was:", ' '.join(map(card_str, last_decision[0])), "vs dealer", last_decision[1])
        print("Basic strategy would have recommended:", recommend(last_decision[0], last_decision[1]))
        return per_hand_bet, -per_hand_bet


def main():
    print("Terminal Blackjack — basic strategy helper")
    try:
        player_bank = float(input("Enter your starting bankroll (e.g. 100): ").strip())
    except Exception:
        player_bank = 100.0
    try:
        dealer_bank = float(input("Enter dealer bankroll (e.g. 1000): ").strip())
    except Exception:
        dealer_bank = 1000.0

    print(f"Starting: Player ${player_bank:.2f} | Dealer ${dealer_bank:.2f} | Bet per round: ${DEFAULT_BET:.2f}")

    while True:
        player_bank, dealer_bank = play_round(player_bank, dealer_bank, bet=DEFAULT_BET)
        print(f"Balances: Player ${player_bank:.2f} | Dealer ${dealer_bank:.2f}")
        if player_bank < DEFAULT_BET:
            print("You don't have enough money to continue. Game over.")
            break
        if input("Play again? (y/n): ").strip().lower() not in ('y','yes'):
            break


if __name__ == '__main__':
    main()
