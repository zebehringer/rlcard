# RF

RF is a custom card game added to RLCard. Players take turns flipping one shared card and deciding where it goes. Making the 5-card **track** a flush earns chips, and the **first player to deposit all 7 of their chips wins**.

The game is a work in progress. The throne and royals can be placed but have no effect yet (see [Planned changes](#planned-changes)).

## Rules

### Deck: 52 cards

| Group | Cards | Count |
|---|---|---|
| Number | 2–9 and T in each suit (`s`, `d`, `h`, `c`) | 36 |
| Royal | `q` and `k` in each suit | 8 |
| Wild | one `w` per suit (wilds have a suit) | 4 |
| Action | 2× Skip (`s`), 2× Ace in the hole (`a`), no suit | 4 |

Cards are written as `<trait>-<suit>`, for example `7-h`, `T-s`, `k-d` or `w-c`. Action cards are just `s` or `a`.

### Setup

- **Track:** 5 cards, drawn until 5 number or wild cards come up.
- **Throne:** one royal.
- **Each player:** one royal.

Cards skipped during setup are shuffled back into the deck. Each player starts with 7 chips out and 0 in. Player hands exist in the code but are never dealt.

### A turn

1. **Flip.** The top card becomes the `target`.
   - **Skip:** the current player loses their turn; play passes on and the game flips again.
   - **Ace:** the current player deposits a chip, play passes on, and the game flips again. If that was their 7th chip, the game ends immediately.
2. **Decide.** The current player chooses what to do with the target:
   - **Number or wild:** replace track slot 0–4, or discard.
   - **Royal:** replace the throne, replace any player's royal (including their own), or discard.
3. **Score.** After a track replacement:
   - **Flush (all 5 the same suit):** +1 chip.
   - **Straight flush:** +2 chips.
   - **Plain straight:** nothing.
4. **Win check.** A player with 7 chips in wins. Otherwise play passes to the next player and a new card is flipped.

Straights: wilds fill gaps (`2 3 w 5 6` counts), ranks can't repeat, and T sits above 9. A flush that stays on the track pays out again to every player who keeps it a flush. That's intended for now; the royal rules are expected to change it.

**Payoffs:** 1 for the winner, 0 for everyone else.

**Players:** 2–5, default 4. Other counts raise a `ValueError` from `RFGame.configure()`.

## Code layout

| File | Contents |
|---|---|
| `card.py` | `RFCard` (type, suit, trait, cached `str`, `rank`) and the console printing used by the human agent |
| `dealer.py` | Shuffles and deals from the deck |
| `player.py` | Chips (`chips_out`, `chips_in`, `deposit_chip`), royal, an unused `hand` |
| `round.py` | Setup, `flip_top_card` (Skip and Ace), `proceed_round` (applies an action), `check_winner`, `get_state` |
| `judger.py` | Winner = any player with 7 chips in |
| `game.py` | `RFGame`: action space, `configure`, step and step back, payoffs, player limits |
| `utils.py` | `init_deck`, `evaluate_cards` / `is_straight`, observation encoders |

Related files outside this folder:
- **Env:** `rlcard/envs/rf.py`, registered as `rlcard.make('rf')`.
- **Human agent:** `rlcard/agents/human_agents/rf_human_agent.py`.
- **Scripts:** `examples/human/rf_human.py`, `examples/run_dmc.py`, `examples/evaluate.py`.

There are no rf tests in `tests/`.

### Discard pile bookkeeping

`played_cards` is the discard pile, and it's shuffled back in when the deck runs out. Only action cards go onto it when flipped. Every other card goes onto it once, in `proceed_round`, when it's discarded or replaced on the table. Adding a card in both places duplicates it on every reshuffle (this bug used to exist), so the deck, discard pile, track, throne, royals and the current non-action target must always add up to 52 cards.

## Actions

The action space is fixed for a given player count and built in `RFGame.init_action_space()`:

| Target | Action strings |
|---|---|
| Number or wild | `<card>_rt0` … `<card>_rt4` (replace track slot), `<card>_d` (discard) |
| Royal | `<card>_thr` (throne), `<card>_p0` … `<card>_p<N-1>` (player's royal), `<card>_d` |

That gives 288 actions with 4 players (272 / 280 / 288 / 296 for 2–5 players). `game.action_ids` maps an action string to its ID. `proceed_round` parses the slot or player number from fixed positions in the string, which works because every card string is 3 characters long.

## Observation (`RFEnv._extract_state`)

The observation has shape `(8 + num_players, 4, 12)`. Each plane is a 4 suits × 12 ranks grid (2–9, T, q, k, w):

| Plane | Contents |
|---|---|
| 0 | Target (empty when the target is an action card) |
| 1 | Throne |
| 2 | Own royal |
| 3–7 | Track slots 0–4, in order |
| 8 … 8+N−1 | Chips in for each player, starting with the observing player and going in turn order; a count of N fills the first N cells |

Other players' royals and the discard pile are **not** encoded. The royal encoding is commented out in `rf.py`, ready for when royals matter. Changing the planes changes `state_shape`, so any saved model has to be retrained.

The raw state (`raw_obs`) also includes `seat_chips_in`, `royals`, `played_cards` and `legal_actions` as strings. `throne` is an `RFCard` object rather than a string.

## Running

Use the project venv:

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e '.[torch]'
```

Without the venv or `PYTHONPATH=.`, running scripts in `examples/` with the shared pyenv Python fails with `No module named 'rlcard.agents'`, because a leftover `rlcard` folder in that Python's site-packages is found first.

```bash
# Play as player 0 against 3 random players (also the VS Code launch config)
python -m examples.human.rf_human

# Play against trained agents: one entry per opponent seat, a model or random
python -m examples.human.rf_human --models experiments/dmc_result/rf/1_<frames>.pth random random

# Train with DMC self-play (CPU, runs until Ctrl-C, saves every 30 min, resume with --load_model)
python examples/run_dmc.py --env rf --xpid rf --num_actors 5

# Evaluate seat 0 against random agents (random play wins ~25% with 4 players)
python examples/evaluate.py --env rf --device cpu --num_games 2000 \
  --models experiments/dmc_result/rf/0_<frames>.pth random random random
```

Notes:
- **One model per seat:** DMC saves one agent per seat (`<seat>_<frames>.pth`), so use the seat-k model for seat k.
- **Player count:** `run_dmc.py` doesn't pass `game_num_players`, so training always uses 4 players.
- **Loading models:** saved agents are whole pickled objects, so `torch.load` needs `weights_only=False` on PyTorch 2.6 and later. `map_location` decides where the weights go; the agent's `set_device` only moves its inputs.
- **Use the CPU:** for this small network the CPU is about 3× faster than Apple's GPU backend (`mps`), because each move is one tiny batch that has to wait for its result. Hence `--device cpu`.
- **Training logs:** DMC's `mean_episode_return_<seat>` is from self-play and stays near 0.25. Measure progress against random agents with `evaluate.py` instead.

## Performance

The env takes roughly 28 µs per decision with random agents. The game rules (`proceed_round`, flipping, scoring) are only about 7% of that; most of the time goes into building the state and observation. During DMC training the network takes about 270 µs per decision, so env speed matters little there.

To check that a change doesn't affect gameplay, run seeded games (`set_seed(n)` plus `config={'seed': n}`) before and after, and compare observations, legal actions, raw states and payoffs. When hashing raw states, convert cards to their `.str` first. Otherwise the `throne` object's printed form includes a memory address, and the hashes differ even between identical runs.

## Planned changes

- **Royals:** the throne and royals will affect the track and chips, to add strategy. With random play, about 97% of games are currently won by an Ace chip. When this lands, other players' royals will likely need to go into the observation.
- **Hands:** `hand`, `num_cards` and the hand printing in the human agent are placeholders. No cards are dealt.
