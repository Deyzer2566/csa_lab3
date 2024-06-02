b =_start
first: word 1
second: word 2
limit: word 4000000
_start:
    and r3, 0
    add r3, 2
    ldr r4, [=limit]
loop:
    ldr r0, [=first]
    ldr r1, [=second]
    add r0, r1
    str r1, [=first]
    str r0, [=second]

    cmp r0, r4
    bnn =_end

    mov r2, r0
    and r2, 1
    addz r3, r0
    b =loop
_end:
    halt