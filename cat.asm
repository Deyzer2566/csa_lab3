b =_start
b =_int_handler
out_register: word 0xfffffc
in_register: word 0xfffffd
_start:
    b =_start
_int_handler:
    push r0
    push r1
    push r2

    ldr r0, [=in_register]
    ldr r1, [=out_register]
    ldr r2, [r0]
    cmp r2, 0
    haltz
    str r2, [r1]
    or r2, -1
    str r2, [r0]

    pop r2
    pop r1
    pop r0
    exint