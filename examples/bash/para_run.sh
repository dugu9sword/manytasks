function para_run {
    total_num=$1;   shift 1
    log=$1;         shift 1
    case $log in  
        on)   $@                 & ;;  
        off)  $@ 2>&1 >/dev/null & ;;  
        *)  exit ;;  
    esac

    while true; do
        local current_number=$(jobs -pr | wc -l)
        if [[ $current_number -lt $total_num ]]; then
                break
        fi
        sleep 1
    done
}

function testcase {
    echo 'test' $1
    sleep 1
}

# sequential
testcase 1
testcase 2

# parallel
for i in $(seq 1 20); do
    para_run 10 on testcase $i
done
wait
# para_run