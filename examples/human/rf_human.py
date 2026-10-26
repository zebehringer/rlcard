''' A toy example of playing against random or trained agents on RF

Pass one opponent per seat after yours, either a trained model file or 'random':
    python examples/human/rf_human.py --models experiments/dmc_result/rf/1_<frames>.pth random random
'''
import argparse

import torch

import rlcard
from rlcard.agents.human_agents.rf_human_agent import HumanAgent, _print_action
from rlcard.agents import RandomAgent

parser = argparse.ArgumentParser("Play RF against random or trained agents")
parser.add_argument(
    '--models',
    nargs='*',
    default=[],
    help='Opponent for each seat after yours: a model file or random (missing seats are random)',
)
args = parser.parse_args()

# Make environment
env = rlcard.make('rf')
if len(args.models) > env.num_players - 1:
    parser.error('at most {} opponents'.format(env.num_players - 1))

agents = [HumanAgent(env.num_actions)]
for seat in range(1, env.num_players):
    model_path = args.models[seat-1] if seat-1 < len(args.models) else 'random'
    if model_path == 'random':
        agents.append(RandomAgent(env.num_actions))
    else:
        agent = torch.load(model_path, map_location='cpu', weights_only=False)
        agent.set_device('cpu')
        agents.append(agent)
env.set_agents(agents)

while (True):
    print(">> Start a new game")
    print(env.state_shape)
    print(env.action_shape)

    trajectories, payoffs = env.run(is_training=False)
    # If the human does not take the final action, we need to
    # print other players action
    final_state = trajectories[0][-1]
    action_record = final_state['action_record']
    state = final_state['raw_obs']
    _action_list = []
    for i in range(1, len(action_record)+1):
        _action_list.insert(0, action_record[-i])
        if action_record[-i][0] == state['current_player']:
            break
    for pair in _action_list:
        print('>> Player', pair[0], 'chose ', end='')
        _print_action(pair[1])
        print('')

    print('===============     Result     ===============')
    if payoffs[0] > 0:
        print('You win!')
    else:
        print('You lose!')
    print('')
    input("Press any key to continue...")
