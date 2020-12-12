from multiprocessing import Manager

manager = Manager()
cuda_num = manager.dict()
cuda_lock = manager.Lock()


def acquire_cuda():
    with cuda_lock:
        min_cuda_idx = -1
        min_cuda_task_num = 1000
        for cuda_idx in cuda_num.keys():
            if cuda_num[cuda_idx] < min_cuda_task_num:
                min_cuda_idx = cuda_idx
                min_cuda_task_num = cuda_num[cuda_idx]
        # log("Current CUDA usage {}, select {}".format(
        #     cuda_num, min_cuda_idx))
        cuda_num[min_cuda_idx] += 1
    return min_cuda_idx


def release_cuda(cuda_idx):
    with cuda_lock:
        cuda_num[cuda_idx] -= 1
