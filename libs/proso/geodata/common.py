# -*- coding: utf-8 -*-
import math
import datetime


UNIX_EPOCH = datetime.datetime(1970, 1, 1, 0, 0)


def normed_prob_diff(expected, given):
    diff = expected - given
    sign = 1 if diff > 0 else -1
    normed_diff = abs(diff) / abs(expected - 0.5 + sign * 0.5)
    return normed_diff


def counter(key, counter_dict):
    count = counter_dict.get(key, 0)
    counter_dict[key] = count + 1
    return count


def correctness(answer):
    return answer['place_asked'] == answer['place_answered']


def random_factor(answer):
    number_of_options = answer['number_of_options']
    if number_of_options == 0:
        return 0
    return 1.0 / (number_of_options)


def theta(prob):
    return - math.log((1 - max(0.01, min(0.99, prob))) / max(0.01, prob))


def sigmoid(x):
    return 1 / (1 + math.exp(- x))


def sigmoid_shift(x, c):
    return c + (1 - c) * sigmoid(x)
