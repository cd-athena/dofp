#include <stdlib.h>
#include <stdio.h>
#include "gurobi_c.h"
#include <stdbool.h>

int
getMaxMinJCoefficients(unsigned n_rep, unsigned n_seg, unsigned n_par, unsigned seg_dur, double bandwidth, const int* bitrates, double* available_times, unsigned* min_q, double* sol, bool isMultiStream);