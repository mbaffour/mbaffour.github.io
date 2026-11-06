set encoding iso_8859_1
set xrange [1:91]
set yrange [0.83:0.85]
set autoscale xfix
set ter png enh interlace size 2400,840 font 'Nimbus,40'
set xlabel 'Position'
set ylabel 'Reliability           ' 
set ytics nomirror 0.4,0.1,0.7
set out '/static/tmp/tmp_7JWBix/rst_zVa6d4/seq_0///Topcons/topcons.large.png'
set tmargin 1.3
set lmargin 11.5
set rmargin 6.5
set label 'TOPCONS' font 'Nimbus,42' at screen 0.022,0.775
set object 1 rect from 30.5,0.781375 to 91.5,0.78625 fc rgb "blue" fs noborder
set object 2 rect from 0.5,0.76 to 30.5,0.78625 fc rgb "black" fs noborder
plot '/static/tmp/tmp_7JWBix/rst_zVa6d4/seq_0///Topcons/reliability.final' w l t '' lc rgb "black" lw 4
exit
