# Copyright (c) 2020 PaddlePaddle Authors. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import unittest

import numpy as np
from eager_op_test import check_out_dtype, paddle_static_guard

import paddle
import paddle.nn.functional as F
from paddle import base
from paddle.base import core


def adaptive_start_index(index, input_size, output_size):
    return int(np.floor(index * input_size / output_size))


def adaptive_end_index(index, input_size, output_size):
    return int(np.ceil((index + 1) * input_size / output_size))


def max_pool1D_forward_naive(
    x,
    ksize,
    strides,
    paddings,
    global_pool=0,
    ceil_mode=False,
    exclusive=False,
    adaptive=False,
    data_type=np.float64,
):
    N, C, L = x.shape
    if global_pool == 1:
        ksize = [L]
    if adaptive:
        L_out = ksize[0]
    else:
        L_out = (
            (L - ksize[0] + 2 * paddings[0] + strides[0] - 1) // strides[0] + 1
            if ceil_mode
            else (L - ksize[0] + 2 * paddings[0]) // strides[0] + 1
        )

    out = np.zeros((N, C, L_out))
    for i in range(L_out):
        if adaptive:
            r_start = adaptive_start_index(i, L, ksize[0])
            r_end = adaptive_end_index(i, L, ksize[0])
        else:
            r_start = np.max((i * strides[0] - paddings[0], 0))
            r_end = np.min((i * strides[0] + ksize[0] - paddings[0], L))
        x_masked = x[:, :, r_start:r_end]

        out[:, :, i] = np.max(x_masked, axis=(2))
    return out


class TestPool1D_API(unittest.TestCase):
    def setUp(self):
        np.random.seed(123)
        self.places = [base.CPUPlace()]
        if core.is_compiled_with_cuda():
            self.places.append(base.CUDAPlace(0))

    def check_adaptive_max_dygraph_results(self, place):
        with base.dygraph.guard(place):
            input_np = np.random.random([2, 3, 32]).astype("float32")
            input = base.dygraph.to_variable(input_np)
            result = F.adaptive_max_pool1d(input, output_size=16)

            result_np = max_pool1D_forward_naive(
                input_np, ksize=[16], strides=[0], paddings=[0], adaptive=True
            )
            np.testing.assert_allclose(result.numpy(), result_np, rtol=1e-05)

            ada_max_pool1d_dg = paddle.nn.layer.AdaptiveMaxPool1D(
                output_size=16
            )
            result = ada_max_pool1d_dg(input)
            np.testing.assert_allclose(result.numpy(), result_np, rtol=1e-05)

    def check_adaptive_max_static_results(self, place):
        with paddle_static_guard():
            with base.program_guard(base.Program(), base.Program()):
                input = paddle.static.data(
                    name="input", shape=[2, 3, 32], dtype="float32"
                )
                result = F.adaptive_max_pool1d(input, output_size=16)

                input_np = np.random.random([2, 3, 32]).astype("float32")
                result_np = max_pool1D_forward_naive(
                    input_np,
                    ksize=[16],
                    strides=[2],
                    paddings=[0],
                    adaptive=True,
                )

                exe = base.Executor(place)
                fetches = exe.run(
                    base.default_main_program(),
                    feed={"input": input_np},
                    fetch_list=[result],
                )
                np.testing.assert_allclose(fetches[0], result_np, rtol=1e-05)

    def test_adaptive_max_pool1d(self):
        for place in self.places:
            self.check_adaptive_max_dygraph_results(place)
            self.check_adaptive_max_static_results(place)


class TestOutDtype(unittest.TestCase):
    def test_max_pool(self):
        api_fn = F.adaptive_max_pool1d
        shape = [1, 3, 32]
        check_out_dtype(
            api_fn,
            in_specs=[(shape,)],
            expect_dtypes=['float32', 'float64'],
            output_size=16,
        )


if __name__ == '__main__':
    unittest.main()
