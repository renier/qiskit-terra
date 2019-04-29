# -*- coding: utf-8 -*-

# Copyright 2019, IBM.
#
# This source code is licensed under the Apache License, Version 2.0 found in
# the LICENSE.txt file in the root directory of this source tree.

# pylint: disable=invalid-name,assignment-from-no-return
"""
Arbitrary unitary circuit instruction.
"""

import numpy

from qiskit.circuit import CompositeGate
from qiskit.circuit import Gate
from qiskit.circuit import QuantumCircuit
from qiskit.circuit import QuantumRegister
from qiskit.quantum_info.operators.predicates import matrix_equal
from qiskit.quantum_info.operators.predicates import is_unitary_matrix
from qiskit.quantum_info.synthesis.two_qubit_kak import two_qubit_kak
from qiskit.extensions.exceptions import ExtensionError


class UnitaryGate(Gate):
    """Class for representing unitary gates"""

    def __init__(self, data, label=None):
        """Create a gate from a numeric unitary matrix.

        Args:
            data (matrix or Operator): unitary operator.
            label (str): unitary name for backend [Default: None].

        Raises:
            ExtensionError: if input data is not an N-qubit unitary operator.
        """
        if hasattr(data, 'to_matrix'):
            # If input is Gate subclass or some other class object that has
            # a to_matrix method this will call that method.
            data = data.to_matrix()
        elif hasattr(data, 'to_operator'):
            # If input is a BaseOperator subclass this attempts to convert
            # the object to an Operator so that we can extract the underlying
            # numpy matrix from `Operator.data`.
            data = data.to_operator().data
        # Convert to numpy array incase not already an array
        data = numpy.array(data, dtype=complex)
        # Check input is unitary
        if not is_unitary_matrix(data):
            raise ExtensionError("Input matrix is not unitary.")
        # Check input is N-qubit matrix
        input_dim, output_dim = data.shape
        n_qubits = int(numpy.log2(input_dim))
        if input_dim != output_dim or 2**n_qubits != input_dim:
            raise ExtensionError(
                "Input matrix is not an N-qubit operator.")
        # Store instruction params
        super().__init__('unitary', n_qubits, [data], label=label)

    def __eq__(self, other):
        if not isinstance(other, UnitaryGate):
            return False
        if self.label != other.label:
            return False
        # Should we match unitaries as equal if they are equal
        # up to global phase?
        return matrix_equal(self.params[0], other.params[0], ignore_phase=True)

    def to_matrix(self):
        """Return matrix for unitary"""
        return self.params[0]

    def inverse(self):
        """Return the adjoint of the Unitary."""
        return self.adjoint()

    def conjugate(self):
        """Return the conjugate of the Unitary."""
        return UnitaryGate(numpy.conj(self.to_matrix()))

    def adjoint(self):
        """Return the adjoint of the unitary."""
        return self.transpose().conjugate()

    def transpose(self):
        """Return the transpose of the unitary."""
        return UnitaryGate(numpy.transpose(self.to_matrix()))

    def _define(self):
        """Calculate a subcircuit that implements this unitary."""
        if self.num_qubits == 2:
            self.definition = two_qubit_kak(self.to_matrix())


def unitary(self, obj, qubits, label=None):
    """Apply u2 to q."""
    if isinstance(qubits, QuantumRegister):
        qubits = qubits[:]
    return self.append(UnitaryGate(obj, label=label), qubits, [])


QuantumCircuit.unitary = unitary
CompositeGate.unitary = unitary