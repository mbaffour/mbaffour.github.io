set encoding iso_8859_1
set xrange [1:32]
set yrange [0.83:0.8]
set autoscale xfix
set ter png enh interlace size 2400,840 font 'Nimbus,40'
set xlabel 'Position'
set ylabel 'Reliability           ' 
set ytics nomirror 0.5,0.1,0.7
set out '/static/tmp/tmp_08ru7U/rst_q8De_G/seq_0///Topcons/topcons.large.png'
set tmargin 1.3
set lmargin 11.5
set rmargin 6.5
set label 'TOPCONS' font 'Nimbus,42' at screen 0.022,0.775
set object 1 rect from 0.5,0.74 to 1.5,0.74325 fc rgb "red" fs noborder
set object 2 rect from 22.5,0.75425 to 32.5,0.7575 fc rgb "blue" fs noborder
set object 3 rect from 1.5,0.74 to 22.5,0.7575 fc rgb "grey" fs noborder
set object 4 rect from 1.5,0.74 to 22.5,0.7575 fc rgb "grey" fs noborder
plot '/static/tmp/tmp_08ru7U/rst_q8De_G/seq_0///Topcons/reliability.final' w l t '' lc rgb "black" lw 4
exit
