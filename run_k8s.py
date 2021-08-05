import time

from jina import Flow, Executor, requests, DocumentArray, Document

# TODO just used for some benchmarking, remove this file before merging

class MyDummyExecutor(Executor):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._docs = DocumentArray()

    @requests(on='/index')
    def index(self, docs, **kwargs):
        self._docs.extend(docs)

    @requests(on='/search')
    def search(self, docs, **kwargs):
        return self._docs

def run_normal(grpc_data_requests, requests):
    # grpc_data_requests=True
    with Flow(port_expose=12345,grpc_data_requests=grpc_data_requests)\
            .add(name='myexec1', parallel=1, uses=MyDummyExecutor)\
            .add(parallel=1, uses=MyDummyExecutor) \
            .add(parallel=1, uses=MyDummyExecutor) \
            .add(parallel=1, uses=MyDummyExecutor) \
            .add(parallel=1, uses=MyDummyExecutor) \
            .add(parallel=1, uses=MyDummyExecutor) \
            .add(parallel=1, uses=MyDummyExecutor) \
            .add(parallel=1, uses=MyDummyExecutor)\
            .add(parallel=1, uses=MyDummyExecutor) as f:

        #print(f._get_routing_table().json())
        print('index')

        for i in range(10):
            result = f.index(DocumentArray([Document(content='1'), Document(content='2')]))
        print(f'indexed {result}')
        print('search')
        da = DocumentArray([Document(content='1')])
        start = time.time()
        for i in range(requests):
            result = f.search(da)
        return time.time()-start

def runq_k8s():
    with Flow(port_expose=12345, k8s=True, host='gateway-service.default.svc.cluster.local')\
            .add(name='myexec1', uses='k8s://my-dummy-executor-image', host='myexec1-service.default.svc.cluster.local') as f:

        print(f._get_routing_table().json())
        print('index')
        for i in range(100):
            f.index(DocumentArray([Document(content='1'), Document(content='2')]))
            print(f'got result {i}')
        print(f'indexed {i}')

        for j in range(100):
            f.index(DocumentArray([Document(content='1'), Document(content='2')]))
            print(f'got result {j+i}')

        for k in range(100):
            f.index(DocumentArray([Document(content='1'), Document(content='2')]))
            print(f'got result {j + i+k}')
        print('search')
        result = f.search(DocumentArray([Document(content='1')]), on_done=print)

requests = 1000
grpc = run_normal(grpc_data_requests=True, requests=requests)
zmq = run_normal(grpc_data_requests=False, requests=requests)

print(f'for {requests} it took:')
print(f'grpc: {grpc} s, avg {(grpc/requests) * 1000} ms')
print(f'zmq: {zmq} s, avg {(zmq/requests) * 1000} ms')

diff = (grpc/requests - zmq/requests)
p = diff * 100 / (zmq/requests)
print(f'diff for avg is {diff * 1000} ms, relative change {round(p, 2)} %')
#run_k8s()