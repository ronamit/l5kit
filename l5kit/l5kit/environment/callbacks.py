import os
import pickle
from stable_baselines3.common.callbacks import BaseCallback
import gym
import numpy as np

class VizCallback(BaseCallback):
    """
    Callback for visualizing current model every ``save_freq`` calls
    to ``env.step()``.

    .. warning::

      When using multiple environments, each call to  ``env.step()``
      will effectively correspond to ``n_envs`` steps.
      To account for that, you can use ``save_freq = max(save_freq // n_envs, 1)``

    :param save_freq:
    :param save_path: Path to the folder where the viz will be saved.
    :param name_prefix: Common prefix to the saved viz
    :param verbose:
    """

    def __init__(self, save_freq: int, save_path: str, name_prefix: str = "rl_model_viz", verbose: int = 0):
        super(VizCallback, self).__init__(verbose)
        self.save_freq = save_freq
        self.save_path = save_path
        self.name_prefix = name_prefix

        self.eval_env = gym.make("L5-v0")

    def _init_callback(self) -> None:
        # Create folder if needed
        if self.save_path is not None:
            os.makedirs(self.save_path, exist_ok=True)

    def _on_step(self) -> bool:
        if self.n_calls % self.save_freq == 0:
            path = os.path.join(self.save_path, f"{self.name_prefix}_{self.num_timesteps}_steps")
            obs = self.eval_env.reset()
            for i in range(350):
                action, _ = self.model.predict(obs, deterministic=True)
                obs, _, done, info = self.eval_env.step(action)
                # print(i)
                if done:
                    break

            # print("Loop Done")
            if self.verbose > 1:
                print(f"Saving viz to {path}")
            
            with open(path + ".pkl", 'wb') as f:
                pickle.dump(info["info"], f)

        return True

class TrajectoryCallback(BaseCallback):
    """
    Callback for saving trajectory at end of training.

    :param save_freq:
    :param save_path: Path to the folder where the viz will be saved.
    :param name_prefix: Common prefix to the saved viz
    :param verbose:
    """

    def __init__(self, save_path: str, name_prefix: str = "rl_model_traj", verbose: int = 0):
        super(TrajectoryCallback, self).__init__(verbose)
        self.save_path = save_path
        self.name_prefix = name_prefix

    def _init_callback(self) -> None:
        # Create folder if needed
        if self.save_path is not None:
            os.makedirs(self.save_path, exist_ok=True)

    def _on_step(self) -> bool:
        pass

    def _on_training_end(self) -> bool:
        path = os.path.join(self.save_path, f"{self.name_prefix}_{self.num_timesteps}_steps")
        obs = self.model.eval_env.reset()
        action_list = []
        gt_action_list = []
        done = False
        for i in range(350):
            # print(i, done, self.eval_env.frame_index, self.eval_env.ego_input_dict["target_positions"])
            gt_action_list.append(self.model.eval_env.ego_input_dict["target_positions"][0, 0])

            action, _ = self.model.predict(obs, deterministic=True)
            obs, _, done, info = self.model.eval_env.step(action)
            action_list.append(action[:2])
            if done:
                break

        action_list = np.stack(action_list)
        gt_action_list = np.stack(gt_action_list)

        error = np.square(action_list - gt_action_list).sum() / len(action_list)
        error = np.sqrt(error)
        print("Error: ", error)
        with open(path + ".pkl", 'wb') as f:
            pickle.dump([gt_action_list, action_list], f)

        return True