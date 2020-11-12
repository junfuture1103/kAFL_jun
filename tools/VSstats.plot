# kAFL Status Plot
#
# Adopted from Redqueen kAFL-Fuzzer/common/evaluation.py
#
# Copyright 2019 Sergej Schumilo, Cornelius Aschermann
# Copyright 2020 Intel Corporation
#
# SPDX-License-Identifier: AGPL-3.0-or-later
#

# Launch as:
# $ gnuplot -c $tools/stats.plot $perform_dir/stats_1.csv $perform_dir/stats_2.csv

indata1=ARG1
indata2=ARG2

set terminal wxt size 900,800 enhanced persist
set multiplot

set grid xtics linetype 0 linecolor rgb '#d0d0d0'
set grid ytics linetype 0 linecolor rgb '#d0d0d0'
set border linecolor rgb '#50c0f0'
set tics textcolor rgb '#000000'
set key outside
set size 1, 0.30
set datafile separator ';'

# auto-scale y axis but avoid empty [0:0] yrange warning when no values yet
set yrange [-0.1:*]

#set xlabel "Time"
set xdata time
set format x "%H:%M:%s"
set timefmt "%s"
set style line 2
set style data line
set origin 0.0,0.66

## plot #1
plot indata1 using 1:2 title 'Total_execs_1' with line linecolor rgb '#0090ff' linewidth 4 smooth bezier, \
indata2 using 1:2 title 'Total_execs_2' with line linecolor rgb '#FF0000' linewidth 4 smooth bezier

## plot #2
set origin 0.0,0.33
plot indata1 using 1:3 title 'Paths Total_1' with lines linecolor rgb '#0090ff' linewidth 2, \
indata1 using 1:4 title 'Favs Total_1' with lines linecolor rgb '#00D8FF' linewidth 2, \
indata2 using 1:3 title 'Paths Total_2' with lines linecolor rgb '#FF0000' linewidth 2, \
indata2 using 1:4 title 'Favs Total_2' with lines linecolor rgb '#D9418C' linewidth 2

## plot #3
set origin 0.0,0.0
plot indata1 using 1:5 title 'Unique Crashes_1' with lines linecolor rgb '#5F00FF' linewidth 2, \
indata2 using 1:5 title 'Unique Crashes_2' with lines linecolor rgb '#3DB7CC' linewidth 2

## plot #4
#set origin 0.0,0.0
#plot indata1 using 0:15 title 'Blacklisted BB' with lines

unset multiplot
#pause 2
#reset
#reread
