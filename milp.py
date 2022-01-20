from __future__ import division
from pulp import *
# import sys
import time

# seg_duration = 4
# bitrate = {1: 200, 2: 500, 3: 1000, 4: 2000, 5: 5000}
#
# omega = 10000
# qi = {1: 2, 2: 3, 3: 2, 4: 1, 5: 1}
# segment = [1, 2, 3, 4, 5]
# deadlines = [1, 5, 9, 13, 17]
# alpha = 0.5
# beta = 0.5

seg_duration = 4
omega = 5000
alpha = 0.5
beta = 0.5
bitrate = {}
qi = {}
segment = []
deadlines = []


########################################################################
def milp_function():
    prob = LpProblem("DoFP", LpMaximize)
    a = LpVariable.dicts("a[(segment,level)]", [(i, j) for i in segment
                                                for j in bitrate.keys() if j >= qi[i]], 0, 1, LpBinary)

    t = LpVariable.dicts("t[(segment)]", [i for i in segment], 0, omega)

    L = LpVariable.dicts("L", [0], 0, 1000000)

    z = LpVariable.dicts("z[(segment-pair,level1,level2)]", [(i, j, k) for i in segment[:-1]
                                                             for j in bitrate.keys() for k in bitrate.keys()
                                                             if j >= qi[i] if k >= qi[i + 1]], 0, 1, LpBinary)

    J = LpVariable.dicts("J", [0], 0, max(bitrate.keys()))

    q_norm_factor = max(bitrate.keys())
    for i in segment:
        q_norm_factor += max(bitrate.keys())

    prob += alpha * (1 / q_norm_factor) * (J[0] + lpSum(a[(i, j)] * j for i in segment for j in bitrate.keys() if j >= qi[i])) - beta * (1 / (1 if len(segment) == 1 else len(segment[:-1]) * max(bitrate.keys()))) * L[0]

    # const 1
    for i in segment:
        c1 = lpSum(a[(i, j)] for j in bitrate.keys() if j >= qi[i]) - 1 == 0
        # print(c1)
        prob += c1

    # const 2
    for i in segment:
        c2 = lpSum(a[(i, j)] * seg_duration * bitrate[j] for j in bitrate.keys() if j > qi[i]) - deadlines[i - 1] * t[
            i] <= 0
        # print(c2)
        prob += c2

    # const 3
    c3 = lpSum(t[i] for i in segment) <= omega
    # print(c3)
    prob += c3

    # const 4
    for i in segment[:-1]:
        for j in bitrate.keys():
            for k in bitrate.keys():
                if j >= qi[i] and k >= qi[i + 1]:
                    # Put 3 constraints
                    # z <= first binary variable
                    c4_1 = z[(i, j, k)] - a[(i, j)] <= 0
                    # print(c4_1)
                    prob += c4_1
                    # z <= second binary variable
                    c4_2 = z[(i, j, k)] - a[(i + 1, k)] <= 0
                    # print(c4_2)
                    prob += c4_2
                    # z >= first + second - 1
                    c4_3 = z[(i, j, k)] - a[(i, j)] - a[(i + 1, k)] >= -1
                    # print(c4_3)
                    prob += c4_3

    # const 5
    c5 = lpSum((z[(i, j, k)]) * abs(k - j) for i in segment[:-1] for j in bitrate.keys() for k in bitrate.keys() if
               j >= qi[i] and k >= qi[i + 1]) - L[0] == 0
    # c5 = lpSum(a[(i, j)] for i in segment[:-1] for j in bitrate.keys() if j >= qi[i]) - L[0] == 0
    # print(c5)
    prob += c5

    # const 6
    for i in segment:
        c6 = J[0] - lpSum(a[(i, j)] * j for j in bitrate.keys() if j >= qi[i]) <= 0
        prob += c6

    LpSolverDefault.msg = 1
    t1 = time.time()
    prob.solve()
    t2 = time.time()-t1
    print(t2)

    # for v in prob.variables():
    #     if v.varValue != 0:
    #         if 'b' in v.name:
    #             t=v.name.replace('b_(client_c,cgroup p, server_s,_quality_q)__(','')
    #             t=t.replace('_','')
    #             t = t.replace(')', '')
    #             [c,s,q]=t.split(',') #client/server/quality
    #             opt_server_num=int(s)
    #             opt_quality_num=int(q)

    v_values = []
    n_useful_par = 2 + len(segment)  # J[0], L[0] and T[i]s
    for i in segment:
        n_useful_par += max(bitrate.keys()) - qi[i] + 1

    count = 0
    for v in prob.variables():
        if count >= n_useful_par:
            break
        # if v.varValue > 0:
        #     print(v.name, "=", v.varValue), v.name[1]
        # print(v.name, "=", v.varValue), v.name[1]
        v_values.append(v.varValue)
        count += 1
    # print(v_values)
    return v_values


def milp_python(group_n, seg_length, throughput, bitrates, av_times, min_q, isMultiStream, weight1, weight2):
    # print("Executing function milp_python!")
    # print("group_n={:d} seg_length={:d} throughput={:.3f}, bitrates={} av_times={} min_q={} "
    #      "isMultiStream={} alpha={:.2f} beta={:.2f}\n".format(group_n, seg_length, throughput, bitrates, av_times,
    #                                                           min_q, isMultiStream, weight1, weight2))
    global segment, seg_duration, omega, bitrate, qi, deadlines, alpha, beta
    for i in range(1, group_n + 1):  # From 1 to group_n
        segment.append(i)
    # print("Segment set = {}".format(segment))
    seg_duration = seg_length
    omega = throughput
    for i in range(len(bitrates)):
        bitrate[i + 1] = bitrates[i]
    # print("Updated bitrates dictionary = {}".format(bitrate))
    for i in range(len(min_q)):
        qi[i + 1] = min_q[i] + 1
    # print("Updated qi dictionary = {}".format(qi))
    for i in range(len(av_times)):
        deadlines.append(av_times[i])
    # print("Deadlines set = {}".format(deadlines))
    alpha = weight1
    beta = weight2
    # print("This is the name of the program:", sys.argv[0])
    # print("Argument List:", str(sys.argv))
    return milp_function()


if __name__ == "__main__":
    print("Executing main!")
    main_res = milp_function()
