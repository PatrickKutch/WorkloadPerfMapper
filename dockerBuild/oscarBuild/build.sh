rm -f -r  Board-Instrumentation-Framework
git clone https://github.com/intel/Board-Instrumentation-Framework.git
# don't need Marvin or Minion
rm -r -f Board-Instrumentation-Framework/Minion
rm -r -f Board-Instrumentation-Framework/Marvin
rm -r -f Board-Instrumentation-Framework/*.pdf


docker build -t patrickkutch/biff-minion-oscar .
docker push patrickkutch/biff-minion-oscar
