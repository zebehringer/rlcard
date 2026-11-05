# RF

RF is a custom card game added to RLCard. Players take turns flipping one shared card and deciding where it goes. Making the 5-card **track** a flush lets you deposit chips, and the **first player to empty their cup wins**.

The game is a work in progress (see [Planned changes](#planned-changes)).

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

Cards skipped during setup are shuffled back into the deck. Each player starts with their own 7 chips in their cup (`chips_out`). Depositing moves one of your own chips from your cup into the shared pot (`chips_in` records the chips you deposited). Every chip remembers its owner, and kings can move chips between cups. No cards are dealt to players. A player can hold at most one card (`hand`), which only `q-d` gives them.

### A turn

1. **Draw.** With `q-h`, if the top discard is not an action card, the player first chooses `draw_discard` (it becomes the `target`) or `draw_deck` (flip). Otherwise the top card of the deck is flipped and becomes the `target`.
   - **Skip:** the current player loses their turn; play passes on and the game flips again.
   - **Ace:** the current player deposits a chip, play passes on, and the game flips again. If that empties their cup, the game ends immediately.
   - **`q-d`:** the player also draws one extra card. Action cards drawn this way go to the discard pile with no effect, and the player draws again.
2. **Decide.** The current player plays one card: the target, an extra card, or their held card.
   - **Number or wild:** replace track slot 0–4, or discard.
   - **Royal:** replace the throne, replace any player's royal (including their own), or discard. Placing a king triggers its effect (see [Royal effects](#royal-effects)).
3. **Hold.** With `q-d`, the player holds one of the cards they didn't play, choosing with `<card>_h` when more than one is left, and the rest are discarded. Without `q-d`, they keep the card they already held, and an unplayed target is discarded.
4. **Score.** After a track replacement:
   - **Flush (all 5 the same suit):** deposit 1 chip.
   - **Straight flush:** deposit 2 chips.
   - **Plain straight:** nothing.
5. **Win check.** A player with an empty cup wins. After a king the winner may not be the current player. If several cups empty at once, the highest seat wins (`judger.py` returns them in seat order and `check_winner` takes the last). Otherwise play passes to the next player and a new card is flipped.

Straights: wilds fill gaps (`2 3 w 5 6` counts), ranks can't repeat, and T sits above 9. A flush that stays on the track pays out again to every player who keeps it a flush. That's intended for now; the royal rules are expected to change it.

**Payoffs:** 1 for the winner, 0 for everyone else.

**Players:** 2–5, default 4. Other counts raise a `ValueError` from `RFGame.configure()`.

### Royal effects

Each of the 8 royals is placed either in front of a player or on the throne, where it applies to everyone. Kings have a one-time effect when placed. Queens have an ongoing effect while they stay in place. Royals dealt during setup have no effect.

**Kings (one-time, `RFRound.apply_king`):**

| Card | In front of a player | On the throne |
|---|---|---|
| `k-s` | The player gives a chip to a random player | Everyone gives a chip to a random player |
| `k-c` | The player gives a chip to the player on their left | Everyone gives a chip to the player on their left |
| `k-h` | The player gives a chip to the player on their right | Everyone gives a chip to the player on their right |
| `k-d` | The player takes 1 of their chips out of any cup other than their own and returns it to theirs (nothing if they can't). If they place it on an opponent's spot, they can also take one of their chips from that opponent's cup and put it into the pot | Everyone else takes 1 of their chips out of any cup and returns it to their own (nothing if they can't) |

How the code reads the king rules:
- "The player" is the one the king is placed in front of. On the throne, "everyone else" (`k-d`) means everyone except the player who placed it.
- Giving a chip moves a chip from your cup into the other player's cup, so it brings you closer to winning. Other players' chips go first, since you can't deposit them. With an empty cup you give nothing. On the throne, everyone gives at once, so a chip you just received can't be passed on.
- Left is the next player in turn order and right is the previous one. A random player is never the giver themselves.
- `k-d` takes the chip back from a random cup that holds one, which is a penalty for whoever takes it back. In the opponent case, the placer's chip goes straight into the pot as a deposit. It is taken after the opponent's chip comes back.

**Queens (ongoing):**

| Card | In front of a player | On the throne |
|---|---|---|
| `q-s` | The player can't deposit chips | No one can deposit chips |
| `q-c` | The player can deposit 1 extra chip per turn | Every player can deposit 1 extra chip per turn |
| `q-d` | The player draws an extra card per turn but still plays only 1 and holds the other | Every player draws an extra card per turn but still plays only 1 and holds the other |
| `q-h` | The player can draw the top card of the discard pile instead of the draw pile | Every player can draw the top card of the discard pile instead of the draw pile |

How the code reads the queen rules:
- A queen applies while it stays on the throne or in front of the player. There is one queen per suit, so the throne queen and a player's own queen are always different, and both apply. For example, `q-c` on the throne and `q-d` in front of a player give that player an extra card and +1 on each deposit.
- `q-s` blocks every deposit: Aces, flushes, and the placer's deposit from `k-d`.
- `q-c` adds 1 to each deposit on the player's turn, so an Ace deposits 2 and a straight flush deposits 3. It doesn't add to `k-d`'s deposit.
- `q-d`: see steps 1 and 3 of [A turn](#a-turn). The held card stays playable on later turns, even after the queen is gone.
- `q-h` isn't offered when the top discard is an action card or the discard pile is empty.

Open questions:
- **TODO:** Decide whether the player who draws a royal can put it in front of another player, or only in front of themselves. The code currently allows any player.
- **TODO:** Decide whether a player can deposit other players' chips from their cup. For now only your own chips can be deposited, so other players' chips can only leave your cup through a king. With queens in, 2,000 random games still all finished (median 450 decisions with 4 players). If other players' chips become depositable, also decide which chip goes first, since there's no action for choosing.
- Should a player choose which cup `k-d` takes from, and who `k-s` gives to? Both are random for now, because there are no actions for those choices.
- Does a throne royal act on its own, or in combination with the state of the track?
- With `q-d`, can the player play both cards instead of holding one?
- Should a player be able to discard their held card, or swap it for the target without `q-d`?

## Code layout

| File | Contents |
|---|---|
| `card.py` | `RFCard` (type, suit, trait, cached `str`, `rank`) and the console printing used by the human agent |
| `dealer.py` | Shuffles and deals from the deck |
| `player.py` | Chips (`chips_out` = cup, `chips_in` = deposited, `deposit_chip`, `pick_chip_to_give`, `take_back_chip`), royal, held card (`hand`) |
| `round.py` | Setup, `start_turn` (`q-h` choice, flip, Skip and Ace), `begin_play` (`q-d` extra card), `proceed_round` (applies an action), `queens` / `deposit`, `apply_king` / `retrieve_chip`, `check_winner`, `get_state` |
| `judger.py` | Winner = any player with an empty cup |
| `game.py` | `RFGame`: action space, `configure`, step and step back, payoffs, player limits |
| `utils.py` | `init_deck`, `evaluate_cards` / `is_straight`, observation encoders |

Related files outside this folder:
- **Env:** `rlcard/envs/rf.py`, registered as `rlcard.make('rf')`.
- **Human agent:** `rlcard/agents/human_agents/rf_human_agent.py`.
- **Scripts:** `examples/human/rf_human.py`, `examples/run_dmc.py`, `examples/evaluate.py`.

There are no rf tests in `tests/`.

### Discard pile bookkeeping

`played_cards` is the discard pile, and it's shuffled back in when the deck runs out. Only action cards go onto it when flipped. Every other card goes onto it once, in `proceed_round`, when it's discarded or replaced on the table. Action cards drawn by `q-d` go onto it when drawn, and leftover cards go onto it at the end of the turn. `draw_discard` takes its top card off. Adding a card in both places duplicates it on every reshuffle (this bug used to exist), so the deck, discard pile, track, throne, royals, held cards, the `q-d` extra card and the target must always add up to 52 cards.

## Actions

The action space is fixed for a given player count and built in `RFGame.init_action_space()`:

| Target | Action strings |
|---|---|
| Number or wild | `<card>_rt0` … `<card>_rt4` (replace track slot), `<card>_d` (discard) |
| Royal | `<card>_thr` (throne), `<card>_p0` … `<card>_p<N-1>` (player's royal), `<card>_d` |
| Hold (`q-d`) | `<card>_h` for every non-action card |
| Draw (`q-h`) | `draw_deck`, `draw_discard` |

The card in a play action can be the target, an extra card or the held card. `RFRound.phase` says which kind of action is legal: `draw`, `play` or `keep`. That gives 338 actions with 4 players (322 / 330 / 338 / 346 for 2–5 players). `game.action_ids` maps an action string to its ID. `proceed_round` parses the slot or player number from fixed positions in the string, which works because every card string is 3 characters long.

## Observation (`RFEnv._extract_state`)

The observation has shape `(11 + num_players, 4, 12)`. Each plane is a 4 suits × 12 ranks grid (2–9, T, q, k, w):

| Plane | Contents |
|---|---|
| 0 | Target (empty before a `q-h` choice and once it's played) |
| 1 | Throne |
| 2 | Own royal |
| 3–7 | Track slots 0–4, in order |
| 8 | `q-d` extra card, until it's played |
| 9 | Own held card |
| 10 | Top of the discard pile (empty when it's an action card) |
| 11 … 11+N−1 | Chips left in each player's cup (any owner), starting with the observing player and going in turn order; a count of N fills the first N cells |

Other players' royals and held cards, the rest of the discard pile and who owns the chips in each cup are **not** encoded (see [Planned changes](#planned-changes)). Changing the planes changes `state_shape`, so any saved model has to be retrained.

The raw state (`raw_obs`) also includes `seat_chips_out`, `royals`, `hand`, `extras`, `discard_top`, `phase`, `played_cards` and `legal_actions` as strings. `chips_out` lists the owner of each chip in the player's own cup. `throne` is an `RFCard` object rather than a string.

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

- **Observation:** with royals in effect, other players' royals (and maybe held cards) should probably go into the observation.
- **Hands:** `num_cards` and the dealer's `deal_cards` are left over. Only `q-d` gives players a card to hold.
- **TODO: special cards in place of the Ts.** Consider replacing some or all of the `T` cards with special cards, such as a "jack squat" (effect to be decided). This would remove the top straight rank (`6 7 8 9 T`), and a special card needs its own 3-character string and actions.
