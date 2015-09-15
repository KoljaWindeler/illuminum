<?php

echo "test:";
exec('ps -ax|grep python/server/main.py| grep -v "grep"',$output,$return_var);
echo $output[0];
?>
