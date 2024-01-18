import sys, qiskit
sys.path.insert(0, '..')
import matplotlib.pyplot as plt
import numpy as np
import qiskit.quantum_info as qi
from qsee.compilation.qsp import QuantumStatePreparation
from qsee.core import ansatz, state, measure
from qsee.backend import constant, utilities
from qsee.evolution import crossover, mutate, selection, threshold
from qsee.evolution.environment import EEnvironment, EEnvironmentMetadata

n = 10
m = 5
num_qubits = 6
utrains, utests = [], []
print("Training states:")
for i in range(0, n):
    utrain = state.haar(num_qubits)
    print(qi.Statevector.from_instruction(utrain).data)
    utrains.append(utrain)
print("Testing states:")
for i in range(0, m):
    utest = state.haar(num_qubits)
    print(qi.Statevector.from_instruction(utest).data)
    utests.append(utest)
    


def random_compilation_fitness(qc: qiskit.QuantumCircuit):
    p0s = []
    for i in range(0, n):
        qsp = QuantumStatePreparation(
            u=qc,
            target_state=utrains[i].inverse()
        ).fit(num_steps=10, metrics_func=['loss_basic'])
        # loss_basic = 1 - p0 => p0 = 1 - loss_basic
        p0s.append(1-qsp.compiler.metrics['loss_basic'][-1])
    # C = 1/n * sum(p_0)
    return np.mean(p0s)

def full_random_compilation_fitness(qc: qiskit.QuantumCircuit):
    p0s = []
    for i in range(0, n):
        qsp = QuantumStatePreparation(
            u=qc,
            target_state=utrains[i].inverse()
        ).fit(num_steps=100, metrics_func=['loss_basic'])
        # loss_basic = 1 - p0 => p0 = 1 - loss_basic
        p0s.append(1-qsp.compiler.metrics['loss_basic'][-1])
    # C = 1/n * sum(p_0)
    return np.mean(p0s)

def random_compiltion_test(qc_best: qiskit.QuantumCircuit):
    risks = []
    for i in range(0, m):
        qsp = QuantumStatePreparation(
            u=qc_best,
            target_state=utests[i].inverse()
        ).fit(num_steps=10)
        # loss_basic = 1 - p0 => p0 = 1 - loss_basic
        risks.append(measure.measure(utests[i]) - measure.measure(qc_best.assign_parameters(qsp.compiler.parameters)))
    # C = 1/n * sum(p_0)
    return np.mean(p0s)


# qubit = 2, depth = 4
# qubit = 3, depth around 15
# qubit = 4, depth around 40
# qubit = 5, depth around 100
# num_generation = 10, 20, 30, ...
# num_circuit = 4, 8, 16, 32, ...
# depth = 2,3,4, ...

def super_evol(_depth, _num_circuit, _num_generation):
    env_metadata = EEnvironmentMetadata(
        num_qubits = num_qubits,
        depth = _depth,
        num_circuit = _num_circuit,
        num_generation = _num_generation,
        prob_mutate=3/(_depth * _num_circuit)
    )
    env = EEnvironment(
        metadata = env_metadata,
        fitness_func=[random_compilation_fitness, full_random_compilation_fitness],
        selection_func=selection.elitist_selection,
        crossover_func=crossover.onepoint_crossover,
        mutate_func=mutate.layerflip_mutate,
        threshold_func=threshold.compilation_threshold
    )
    env.set_filename(f'n={num_qubits},d={_depth},n_circuit={_num_circuit},n_gen={_num_generation}')
    env.evol()



num_generations = [10, 20, 30, 40, 50]


def multiple_compile(num_generations):
    import concurrent.futures
    executor = concurrent.futures.ProcessPoolExecutor()
    results = executor.map(bypass_compile, num_generations)
    return results

def bypass_compile(num_generation):
    depths = list(range(30, 40)) # 6 qubits case
    num_circuits = [4, 8, 16, 32]
    for depth in depths:
        for num_circuit in num_circuits:
            print(depth)
            # check if folder exists
            import os
            if os.path.isdir(f'n={num_qubits},d={depth},n_circuit={num_circuit},n_gen={num_generation}') == False:
                print(depth, num_circuit, num_generation)
                super_evol(depth, num_circuit, num_generation)

# main
if __name__ == '__main__':
    multiple_compile(num_generations)