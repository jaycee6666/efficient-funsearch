# implemented by RZ
# profile the experiment using tensorboard

from __future__ import annotations

import json
import logging
import os.path
from typing import Dict

from implementation import code_manipulation
from tensorboardX import (
    SummaryWriter,  # Use tensorboardX instead of torch.utils.tensorboard to avoid large torch dependency
)


class Profiler:
    def __init__(
            self,
            log_dir: str | None = None,
            pkl_dir: str | None = None,
            max_log_nums: int | None = None,
    ):
        """
        Args:
            log_dir     : folder path for tensorboard log files.
            pkl_dir     : save the results to a pkl file.
            max_log_nums: stop logging if exceeding max_log_nums.
        """
        logging.getLogger().setLevel(logging.INFO)
        self._log_dir = log_dir
        self._json_dir = os.path.join(log_dir, 'samples')
        os.makedirs(self._json_dir, exist_ok=True)
        # self._pkl_dir = pkl_dir
        self._max_log_nums = max_log_nums
        self._num_samples = 0
        self._cur_best_program_sample_order = None
        self._cur_best_program_score = -99999999
        self._evaluate_success_program_num = 0
        self._evaluate_failed_program_num = 0
        self._tot_sample_time = 0
        self._tot_evaluate_time = 0
        self._all_sampled_functions: Dict[int, code_manipulation.Function] = {}

        if log_dir:
            self._writer = SummaryWriter(log_dir=log_dir)

        self._each_sample_best_program_score = []
        self._each_sample_evaluate_success_program_num = []
        self._each_sample_evaluate_failed_program_num = []
        self._each_sample_tot_sample_time = []
        self._each_sample_tot_evaluate_time = []

        # Phase 2: Dedup statistics
        self._total_dedup_checks = 0
        self._dedup_filtered = 0
        self._dedup_by_level = {0: 0, 1: 0, 2: 0}
        self._dedup_time_level0 = 0.0
        self._dedup_time_level1 = 0.0
        self._dedup_time_level2 = 0.0

    def _write_tensorboard(self):
        if not self._log_dir:
            return

        self._writer.add_scalar(
            'Best Score of Function',
            self._cur_best_program_score,
            global_step=self._num_samples
        )
        self._writer.add_scalars(
            'Legal/Illegal Function',
            {
                'legal function num': self._evaluate_success_program_num,
                'illegal function num': self._evaluate_failed_program_num
            },
            global_step=self._num_samples
        )
        self._writer.add_scalars(
            'Total Sample/Evaluate Time',
            {'sample time': self._tot_sample_time, 'evaluate time': self._tot_evaluate_time},
            global_step=self._num_samples
        )

    def _write_json(self, programs: code_manipulation.Function):
        sample_order = programs.global_sample_nums
        sample_order = sample_order if sample_order is not None else 0
        function_str = str(programs)
        score = programs.score
        content = {
            'sample_order': sample_order,
            'function': function_str,
            # Record additional fields for later behavioral dedup analysis
            'function_body': programs.body if hasattr(programs, 'body') else None,
            'score': score,
            'sample_time': programs.sample_time if hasattr(programs, 'sample_time') else None,
            'evaluate_time': programs.evaluate_time if hasattr(programs, 'evaluate_time') else None,
        }
        path = os.path.join(self._json_dir, f'samples_{sample_order}.json')
        with open(path, 'w') as json_file:
            json.dump(content, json_file)

    def register_function(self, programs: code_manipulation.Function):
        if self._max_log_nums is not None and self._num_samples >= self._max_log_nums:
            return

        sample_orders: int = programs.global_sample_nums
        if sample_orders not in self._all_sampled_functions:
            self._num_samples += 1
            self._all_sampled_functions[sample_orders] = programs
            self._record_and_verbose(sample_orders)
            self._write_tensorboard()
            self._write_json(programs)
            # Append CSV log for easy pandas one-line loading
            csv_path = os.path.join(self._log_dir, 'run_log.csv')
            write_header = not os.path.exists(csv_path)
            with open(csv_path, 'a') as f:
                if write_header:
                    f.write('sample_order,score,sample_time,evaluate_time,is_duplicate,dedup_level,dedup_time_ms\n')
                sample_time = programs.sample_time if hasattr(programs, 'sample_time') else ''
                evaluate_time = programs.evaluate_time if hasattr(programs, 'evaluate_time') else ''
                score_val = programs.score if programs.score is not None else ''
                # Phase 2: Dedup-related fields
                is_dup = getattr(programs, 'is_duplicate', '')
                dedup_level = getattr(programs, 'dedup_level', '')
                dedup_time = getattr(programs, 'dedup_time_ms', '')
                f.write(f'{programs.global_sample_nums},{score_val},{sample_time},{evaluate_time},{is_dup},{dedup_level},{dedup_time}\n')

    def _record_and_verbose(self, sample_orders: int):
        function = self._all_sampled_functions[sample_orders]
        # function_name = function.name
        # function_body = function.body.strip('\n')
        function_str = str(function).strip('\n')
        sample_time = function.sample_time
        evaluate_time = function.evaluate_time
        score = function.score
        # log attributes of the function
        print('================= Evaluated Function =================')
        print(f'{function_str}')
        print('------------------------------------------------------')
        print(f'Score        : {str(score)}')
        print(f'Sample time  : {str(sample_time)}')
        print(f'Evaluate time: {str(evaluate_time)}')
        print(f'Sample orders: {str(sample_orders)}')
        print('======================================================\n\n')

        # update best function
        if function.score is not None and score > self._cur_best_program_score:
            self._cur_best_program_score = score
            self._cur_best_program_sample_order = sample_orders

        # update statistics about function
        if score:
            self._evaluate_success_program_num += 1
        else:
            self._evaluate_failed_program_num += 1

        if sample_time:
            self._tot_sample_time += sample_time
        if evaluate_time:
            self._tot_evaluate_time += evaluate_time

        # update ...
        # self._each_sample_best_program_score.append(self._cur_best_program_score)
        # self._each_sample_evaluate_success_program_num.append(self._evaluate_success_program_num)
        # self._each_sample_evaluate_failed_program_num.append(self._evaluate_failed_program_num)
        # self._each_sample_tot_sample_time.append(self._tot_sample_time)
        # self._each_sample_tot_evaluate_time.append(self._tot_evaluate_time)

    @property
    def has_dedup_data(self) -> bool:
        """Whether there is dedup data available for reporting."""
        return self._total_dedup_checks > 0

    # ===== Phase 2: Dedup logging =====

    def register_dedup_event(self, dedup_result, **kwargs):
        """Record a dedup check event (addressing TA feedback #5: overhead report).

        Args:
            dedup_result: DedupResult instance
        """
        self._total_dedup_checks += 1
        self._dedup_time_level0 += dedup_result.time_level0
        self._dedup_time_level1 += dedup_result.time_level1
        self._dedup_time_level2 += dedup_result.time_level2

        if dedup_result.is_duplicate and not dedup_result.is_validation_pass:
            self._dedup_filtered += 1
            if dedup_result.level_caught is not None:
                self._dedup_by_level[dedup_result.level_caught] = (
                    self._dedup_by_level.get(dedup_result.level_caught, 0) + 1
                )

        # TensorBoard logging
        if self._log_dir and hasattr(self, '_writer'):
            self._writer.add_scalar(
                'Dedup/filtered_total', self._dedup_filtered,
                global_step=self._total_dedup_checks)
            for level in [0, 1, 2]:
                self._writer.add_scalar(
                    f'Dedup/level{level}_catches',
                    self._dedup_by_level.get(level, 0),
                    global_step=self._total_dedup_checks)

    def dedup_summary(self, avg_eval_time: float = 4.14) -> str:
        """Generate dedup statistics report (addressing TA feedback #5: overhead report format).

        Args:
            avg_eval_time: Average single evaluation time (seconds), used to compute time saved
        """
        passed = self._total_dedup_checks - self._dedup_filtered
        total_dedup_time = (self._dedup_time_level0
                           + self._dedup_time_level1
                           + self._dedup_time_level2)
        saved_time = self._dedup_filtered * avg_eval_time
        net_saving = saved_time - total_dedup_time

        # Compute average time per level
        n = max(self._total_dedup_checks, 1)
        avg_l0 = self._dedup_time_level0 / n * 1000
        avg_l1 = self._dedup_time_level1 / n * 1000
        avg_l2 = self._dedup_time_level2 / n * 1000

        report = (
            f"Dedup Statistics Report:\n"
            f"  Total checks: {self._total_dedup_checks}  |  "
            f"L0 filtered: {self._dedup_by_level.get(0, 0)}  |  "
            f"L1 filtered: {self._dedup_by_level.get(1, 0)}  |  "
            f"L2 filtered: {self._dedup_by_level.get(2, 0)}  |  "
            f"Passed: {passed}\n"
            f"  Avg time per level: L0={avg_l0:.1f}ms  L1={avg_l1:.1f}ms  L2={avg_l2:.1f}ms\n"
            f"  Eval time saved: {self._dedup_filtered} x {avg_eval_time:.2f}s = {saved_time:.1f}s\n"
            f"  Dedup total overhead: {self._total_dedup_checks} x {total_dedup_time / n * 1000:.1f}ms = {total_dedup_time:.2f}s\n"
            f"  Net saving: {net_saving:.1f}s"
        )
        return report
