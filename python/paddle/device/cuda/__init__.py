# Copyright (c) 2021 PaddlePaddle Authors. All Rights Reserved.
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

import paddle
from paddle.base import core
from paddle.base.wrapped_decorator import signature_safe_contextmanager
from paddle.utils import deprecated

from .streams import Stream  # noqa: F401
from .streams import Event  # noqa: F401

__all__ = [
    'Stream',
    'Event',
    'current_stream',
    'synchronize',
    'device_count',
    'empty_cache',
    'max_memory_allocated',
    'max_memory_reserved',
    'memory_allocated',
    'memory_reserved',
    'stream_guard',
    'get_device_properties',
    'get_device_name',
    'get_device_capability',
]


@deprecated(
    since="2.5.0",
    update_to="paddle.device.current_stream",
    level=1,
    reason="current_stream in paddle.device.cuda will be removed in future",
)
def current_stream(device=None):
    '''
    Return the current CUDA stream by the device.

    Args:
        device(paddle.CUDAPlace()|int, optional): The device or the ID of the device which want to get stream from.
                If device is None, the device is the current device. Default: None.

    Returns:
            CUDAStream: the stream to the device.

    Examples:
        .. code-block:: python

            # required: gpu
            import paddle

            s1 = paddle.device.cuda.current_stream()

            s2 = paddle.device.cuda.current_stream(0)

            s3 = paddle.device.cuda.current_stream(paddle.CUDAPlace(0))

    '''

    device_id = -1

    if device is not None:
        if isinstance(device, int):
            device_id = device
        elif isinstance(device, core.CUDAPlace):
            device_id = device.get_device_id()
        else:
            raise ValueError("device type must be int or paddle.CUDAPlace")

    return core._get_current_stream(device_id)


@deprecated(
    since="2.5.0",
    update_to="paddle.device.synchronize",
    level=1,
    reason="synchronize in paddle.device.cuda will be removed in future",
)
def synchronize(device=None):
    '''
    Wait for the compute on the given CUDA device to finish.

    Args:
        device(paddle.CUDAPlace()|int, optional): The device or the ID of the device.
                If device is None, the device is the current device. Default: None.

    Examples:
        .. code-block:: python

            # required: gpu
            import paddle

            paddle.device.cuda.synchronize()
            paddle.device.cuda.synchronize(0)
            paddle.device.cuda.synchronize(paddle.CUDAPlace(0))

    '''

    device_id = -1

    if device is not None:
        if isinstance(device, int):
            device_id = device
        elif isinstance(device, core.CUDAPlace):
            device_id = device.get_device_id()
        else:
            raise ValueError("device type must be int or paddle.CUDAPlace")

    return core._device_synchronize(device_id)


def device_count():
    '''
    Return the number of GPUs available.

    Returns:
        int: the number of GPUs available.

    Examples:
        .. code-block:: python

            import paddle

            paddle.device.cuda.device_count()

    '''

    num_gpus = (
        core.get_cuda_device_count()
        if hasattr(core, 'get_cuda_device_count')
        else 0
    )

    return num_gpus


def empty_cache():
    '''
    Releases idle cached memory held by the allocator so that those can be used in other GPU
    application and visible in `nvidia-smi`. In most cases you don't need to use this function,
    Paddle does not release the memory back to the OS when you remove Tensors on the GPU,
    Because it keeps gpu memory in a pool so that next allocations can be done much faster.

    Examples:
        .. code-block:: python

            import paddle

            # required: gpu
            paddle.set_device("gpu")
            tensor = paddle.randn([512, 512, 512], "float")
            del tensor
            paddle.device.cuda.empty_cache()
    '''

    if core.is_compiled_with_cuda():
        core.cuda_empty_cache()


def extract_cuda_device_id(device, op_name):
    '''
    Return the id of the given cuda device. It is just a utility that will not be exposed to users.

    Args:
        device(paddle.CUDAPlace or int or str): The device, the id of the device or
            the string name of device like 'gpu:x'.
            Default: None.

    Return:
        int: The id of the given device. If device is None, return the id of current device.
    '''
    if device is None:
        return core.get_cuda_current_device_id()

    if isinstance(device, int):
        device_id = device
    elif isinstance(device, core.CUDAPlace):
        device_id = device.get_device_id()
    elif isinstance(device, str):
        if device.startswith('gpu:'):
            device_id = int(device[4:])
        else:
            raise ValueError(
                "The current string {} is not expected. Because {} only support string which is like 'gpu:x'. "
                "Please input appropriate string again!".format(device, op_name)
            )
    else:
        raise ValueError(
            "The device type {} is not expected. Because {} only support int, str or paddle.CUDAPlace. "
            "Please input appropriate device again!".format(device, op_name)
        )

    assert (
        device_id >= 0
    ), f"The device id must be not less than 0, but got id = {device_id}."
    assert (
        device_id < device_count()
    ), f"The device id {device_id} exceeds gpu card number {device_count()}"

    return device_id


def max_memory_allocated(device=None):
    '''
    Return the peak size of gpu memory that is allocated to tensor of the given device.

    Note:
        The size of GPU memory allocated to tensor is 256-byte aligned in Paddle, which may larger than the memory size that tensor actually need.
        For instance, a float32 tensor with shape [1] in GPU will take up 256 bytes memory, even though storing a float32 data requires only 4 bytes.

    Args:
        device(paddle.CUDAPlace or int or str, optional): The device, the id of the device or
            the string name of device like 'gpu:x'. If device is None, the device is the current device.
            Default: None.

    Return:
        int: The peak size of gpu memory that is allocated to tensor of the given device, in bytes.

    Examples:
        .. code-block:: python

            # required: gpu
            import paddle

            max_memory_allocated_size = paddle.device.cuda.max_memory_allocated(paddle.CUDAPlace(0))
            max_memory_allocated_size = paddle.device.cuda.max_memory_allocated(0)
            max_memory_allocated_size = paddle.device.cuda.max_memory_allocated("gpu:0")
    '''
    name = "paddle.device.cuda.max_memory_allocated"
    if not core.is_compiled_with_cuda():
        raise ValueError(
            f"The API {name} is not supported in CPU-only PaddlePaddle. Please reinstall PaddlePaddle with GPU support to call this API."
        )
    device_id = extract_cuda_device_id(device, op_name=name)
    return core.device_memory_stat_peak_value("Allocated", device_id)


def max_memory_reserved(device=None):
    '''
    Return the peak size of GPU memory that is held by the allocator of the given device.

    Args:
        device(paddle.CUDAPlace or int or str, optional): The device, the id of the device or
            the string name of device like 'gpu:x'. If device is None, the device is the current device.
            Default: None.

    Return:
        int: The peak size of GPU memory that is held by the allocator of the given device, in bytes.

    Examples:
        .. code-block:: python

            # required: gpu
            import paddle

            max_memory_reserved_size = paddle.device.cuda.max_memory_reserved(paddle.CUDAPlace(0))
            max_memory_reserved_size = paddle.device.cuda.max_memory_reserved(0)
            max_memory_reserved_size = paddle.device.cuda.max_memory_reserved("gpu:0")
    '''
    name = "paddle.device.cuda.max_memory_reserved"
    if not core.is_compiled_with_cuda():
        raise ValueError(
            f"The API {name} is not supported in CPU-only PaddlePaddle. Please reinstall PaddlePaddle with GPU support to call this API."
        )
    device_id = extract_cuda_device_id(device, op_name=name)
    return core.device_memory_stat_peak_value("Reserved", device_id)


def memory_allocated(device=None):
    '''
    Return the current size of gpu memory that is allocated to tensor of the given device.

    Note:
        The size of GPU memory allocated to tensor is 256-byte aligned in Paddle, which may be larger than the memory size that tensor actually need.
        For instance, a float32 tensor with shape [1] in GPU will take up 256 bytes memory, even though storing a float32 data requires only 4 bytes.

    Args:
        device(paddle.CUDAPlace or int or str, optional): The device, the id of the device or
            the string name of device like 'gpu:x'. If device is None, the device is the current device.
            Default: None.

    Return:
        int: The current size of gpu memory that is allocated to tensor of the given device, in bytes.

    Examples:
        .. code-block:: python

            # required: gpu
            import paddle

            memory_allocated_size = paddle.device.cuda.memory_allocated(paddle.CUDAPlace(0))
            memory_allocated_size = paddle.device.cuda.memory_allocated(0)
            memory_allocated_size = paddle.device.cuda.memory_allocated("gpu:0")
    '''
    name = "paddle.device.cuda.memory_allocated"
    if not core.is_compiled_with_cuda():
        raise ValueError(
            f"The API {name} is not supported in CPU-only PaddlePaddle. Please reinstall PaddlePaddle with GPU support to call this API."
        )
    device_id = extract_cuda_device_id(device, op_name=name)
    return core.device_memory_stat_current_value("Allocated", device_id)


def memory_reserved(device=None):
    '''
    Return the current size of GPU memory that is held by the allocator of the given device.

    Args:
        device(paddle.CUDAPlace or int or str, optional): The device, the id of the device or
            the string name of device like 'gpu:x'. If device is None, the device is the current device.
            Default: None.

    Return:
        int: The current size of GPU memory that is held by the allocator of the given device, in bytes.

    Examples:
        .. code-block:: python

            # required: gpu
            import paddle

            memory_reserved_size = paddle.device.cuda.memory_reserved(paddle.CUDAPlace(0))
            memory_reserved_size = paddle.device.cuda.memory_reserved(0)
            memory_reserved_size = paddle.device.cuda.memory_reserved("gpu:0")
    '''
    name = "paddle.device.cuda.memory_reserved"
    if not core.is_compiled_with_cuda():
        raise ValueError(
            f"The API {name} is not supported in CPU-only PaddlePaddle. Please reinstall PaddlePaddle with GPU support to call this API."
        )
    device_id = extract_cuda_device_id(device, op_name=name)
    return core.device_memory_stat_current_value("Reserved", device_id)


def _set_current_stream(stream):
    '''
    Set the current stream.

    Parameters:
        stream(paddle.device.cuda.Stream): The selected stream.

    Returns:
        CUDAStream: The previous stream.

    '''

    if not isinstance(stream, paddle.device.cuda.Stream):
        raise TypeError("stream type should be paddle.device.cuda.Stream")

    cur_stream = current_stream()
    if id(stream) == id(cur_stream):
        return stream
    return core._set_current_stream(stream)


@deprecated(
    since="2.5.0",
    update_to="paddle.device.stream_guard",
    level=1,
    reason="stream_guard in paddle.device.cuda will be removed in future",
)
@signature_safe_contextmanager
def stream_guard(stream):
    '''
    Notes:
        This API only supports dynamic graph mode currently.

    A context manager that specifies the current stream context by the given stream.

    Parameters:
        stream(paddle.device.cuda.Stream): the selected stream. If stream is None, just yield.

    Examples:
        .. code-block:: python

            # required: gpu
            import paddle

            s = paddle.device.cuda.Stream()
            data1 = paddle.ones(shape=[20])
            data2 = paddle.ones(shape=[20])
            with paddle.device.cuda.stream_guard(s):
                data3 = data1 + data2

    '''

    if stream is not None and not isinstance(stream, paddle.device.cuda.Stream):
        raise TypeError("stream type should be paddle.device.cuda.Stream")

    cur_stream = current_stream()
    if stream is None or id(stream) == id(cur_stream):
        yield
    else:
        pre_stream = _set_current_stream(stream)
        try:
            yield
        finally:
            stream = _set_current_stream(pre_stream)


def get_device_properties(device=None):
    '''
    Return the properties of given device.

    Args:
        device(paddle.CUDAPlace or int or str, optional): The device, the id of the device or
            the string name of device like 'gpu:x' which to get the properties of the
            device from. If device is None, the device is the current device.
            Default: None.

    Returns:
        _gpuDeviceProperties: The properties of the device which include ASCII string
        identifying device, major compute capability, minor compute capability, global
        memory available and the number of multiprocessors on the device.

    Examples:

        .. code-block:: python

            # required: gpu

            import paddle
            paddle.device.cuda.get_device_properties()
            # _gpuDeviceProperties(name='A100-SXM4-40GB', major=8, minor=0, total_memory=40536MB, multi_processor_count=108)

            paddle.device.cuda.get_device_properties(0)
            # _gpuDeviceProperties(name='A100-SXM4-40GB', major=8, minor=0, total_memory=40536MB, multi_processor_count=108)

            paddle.device.cuda.get_device_properties('gpu:0')
            # _gpuDeviceProperties(name='A100-SXM4-40GB', major=8, minor=0, total_memory=40536MB, multi_processor_count=108)

            paddle.device.cuda.get_device_properties(paddle.CUDAPlace(0))
            # _gpuDeviceProperties(name='A100-SXM4-40GB', major=8, minor=0, total_memory=40536MB, multi_processor_count=108)

    '''

    if not core.is_compiled_with_cuda():
        raise ValueError(
            "The API paddle.device.cuda.get_device_properties is not supported in "
            "CPU-only PaddlePaddle. Please reinstall PaddlePaddle with GPU support "
            "to call this API."
        )

    if device is not None:
        if isinstance(device, int):
            device_id = device
        elif isinstance(device, core.CUDAPlace):
            device_id = device.get_device_id()
        elif isinstance(device, str):
            if device.startswith('gpu:'):
                device_id = int(device[4:])
            else:
                raise ValueError(
                    "The current string {} is not expected. Because paddle.device."
                    "cuda.get_device_properties only support string which is like 'gpu:x'. "
                    "Please input appropriate string again!".format(device)
                )
        else:
            raise ValueError(
                "The device type {} is not expected. Because paddle.device.cuda."
                "get_device_properties only support int, str or paddle.CUDAPlace. "
                "Please input appropriate device again!".format(device)
            )
    else:
        device_id = -1

    return core.get_device_properties(device_id)


def get_device_name(device=None):
    '''
    Return the name of the device which is got from CUDA function `cudaDeviceProp <https://docs.nvidia.com/cuda/cuda-runtime-api/group__CUDART__DEVICE.html#group__CUDART__DEVICE_1g1bf9d625a931d657e08db2b4391170f0>`_.

    Parameters:
        device(paddle.CUDAPlace|int, optional): The device or the ID of the device. If device is None (default), the device is the current device.

    Returns:
        str: The name of the device.

    Examples:

        .. code-block:: python

            # required: gpu

            import paddle

            paddle.device.cuda.get_device_name()

            paddle.device.cuda.get_device_name(0)

            paddle.device.cuda.get_device_name(paddle.CUDAPlace(0))

    '''

    return get_device_properties(device).name


def get_device_capability(device=None):
    """
    Return the major and minor revision numbers defining the device's compute capability which are got from CUDA function `cudaDeviceProp <https://docs.nvidia.com/cuda/cuda-runtime-api/group__CUDART__DEVICE.html#group__CUDART__DEVICE_1g1bf9d625a931d657e08db2b4391170f0>`_.

    Parameters:
        device(paddle.CUDAPlace|int, optional): The device or the ID of the device. If device is None (default), the device is the current device.

    Returns:
        tuple(int,int): the major and minor revision numbers defining the device's compute capability.

    Examples:

        .. code-block:: python

            >>> # doctest: +REQUIRES(env:GPU)

            >>> import paddle
            >>> paddle.device.set_device('gpu')
            >>> paddle.device.cuda.get_device_capability()

            >>> paddle.device.cuda.get_device_capability(0)

            >>> paddle.device.cuda.get_device_capability(paddle.CUDAPlace(0))

    """
    prop = get_device_properties(device)
    return prop.major, prop.minor
