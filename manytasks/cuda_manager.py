from multiprocessing import Manager

manager = Manager()
num_tasks_on_cuda = manager.dict()
cuda_lock = manager.Lock()


def acquire_cuda(num=1):
    with cuda_lock:
        sorted_idxs_by_num = sorted(list(num_tasks_on_cuda.items()), key=lambda kv: kv[1])
        cuda_idxs = tuple(list(map(lambda kv: kv[0], sorted_idxs_by_num[:num])))
        for idx in cuda_idxs:
            num_tasks_on_cuda[idx] += 1
    return cuda_idxs


def release_cuda(cuda_idxs):
    with cuda_lock:
        for ele in cuda_idxs:
            num_tasks_on_cuda[ele] -= 1
