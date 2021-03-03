# -*- Python -*-
# This file is licensed under a pytorch-style license
# See frontends/pytorch/LICENSE for license information.

import unittest
from unittest import TestCase

import torch
import torch.nn as nn
import torch.nn.functional as F

import torch_mlir

# RUN: %PYTHON %s | npcomp-opt | FileCheck %s

class ResA(nn.Module):
    def __init__(self, channels):
      C = int(channels)
      C2 = int(channels/2)
      super(ResA, self).__init__()
      self.model = nn.Sequential(# A1
                                nn.BatchNorm2d(C),
                                nn.ReLU(),
                                nn.Conv2d(C,C2,1,stride=1,padding=0,dilation=1,groups=1,bias=True),
                                # B1
                                nn.BatchNorm2d(C2),
                                nn.ReLU(),
                                nn.Conv2d(C2,C2,3,stride=1,padding=1,dilation=1,groups=1,bias=True),
                                # C1
                                nn.BatchNorm2d(C2),
                                nn.ReLU(),
                                nn.Conv2d(C2,C,1,stride=1,padding=0,dilation=1,groups=1,bias=True))
    def forward(self, x):
      res = self.model.forward(x)
      return x + res

mb = torch_mlir.ModuleBuilder()
model = ResA(16)
inputs = torch.ones((1,16,128,128))
with mb.capture_function("resa", [inputs]) as f:
  f.returns([model(inputs)])

# TODO: This isn't a great unit test but checking-in as a lead-in for more
# appropriately factored tests.
# NOTE: Assertions have been autogenerated by utils/generate-test-checks.py
# CHECK-LABEL:   func @resa(
# CHECK-SAME:               %[[VAL_0:.*]]: !numpy.ndarray<[1,16,128,128]:f32>) -> !numpy.ndarray<[1,16,128,128]:f32> {
# CHECK:           %[[VAL_118:.*]] = torch.kernel_call "aten::convolution" {{.*}} : (!numpy.ndarray<[1,8,128,128]:f32>, !numpy.ndarray<[16,8,1,1]:f32>, !numpy.ndarray<[16]:f32>, !basicpy.ListType, !basicpy.ListType, !basicpy.ListType, !basicpy.BoolType, !basicpy.ListType, i64) -> !numpy.ndarray<[1,16,128,128]:f32>
# CHECK:           %[[VAL_119:.*]] = torch.kernel_call "aten::add" %{{.*}}, %[[VAL_118]], %{{.*}}, %{{.*}} : (!numpy.ndarray<[1,16,128,128]:f32>, !numpy.ndarray<[1,16,128,128]:f32>, i64, !numpy.ndarray<[1,16,128,128]:f32>) -> !numpy.ndarray<[1,16,128,128]:f32>
# CHECK:           return %[[VAL_119]] : !numpy.ndarray<[1,16,128,128]:f32>
# CHECK:         }
mb.module.operation.print(large_elements_limit=2)
