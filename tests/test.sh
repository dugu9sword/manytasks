rm -rf *.logs
rm *.log
rm *.json
rm *.rule
cp ../examples/python/*.* .

echo "[TEST INIT]"
echo t1.config | manytasks init config
echo t2.rule | manytasks init rule

echo "[TEST RUN]"
manytasks run tasks | tee t3.normal.log
manytasks run tasks.json --log-path pypy | tee t4.newpath.log
echo o | manytasks run tasks --log-path pypy | tee t5.override.log
echo r | manytasks run tasks --log-path pypy | tee t6.resume.log

echo "[TEST SHOW]"
manytasks show pypy --rule rule | tee t7.show.log
