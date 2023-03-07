vr=0
for i in 1 2 3 4 5; do
    echo $i
    if [ $i -eq 3 ]; then
        vr=1
    fi
done
echo $vr